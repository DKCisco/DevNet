# -*- coding: utf-8 -*-
"""
ip_enricher_whois.py

Same as ip_enricher, but replaces the optional IPinfo dependency with a built-in
legacy WHOIS (port 43) lookup, using the authoritative RIR hinted by RDAP.

Usage:
  python ip_enricher_whois.py --in input.txt --out enriched.csv --aws --debug --timeout 10 --retries 1

Notes:
  - RDAP remains the primary source for authoritative registry ownership.
  - WHOIS is used only to add helpful fields (whois_org, whois_asn, whois_raw_path).
    Parsing is best-effort and varies by RIR formatting.
"""

from __future__ import annotations
import argparse
import csv
import ipaddress
import json
import re
import socket
import sys
import time
from typing import Dict, List, Optional, Tuple

try:
    import httpx  # Preferred
    _USE_HTTPX = True
except Exception:
    import requests
    _USE_HTTPX = False

# ---------------- HTTP helper ----------------

def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 15.0, retries: int = 2, debug: bool = False):
    if _USE_HTTPX:
        last_exc = None
        for attempt in range(retries+1):
            try:
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    if debug: print(f'[DBG] GET {url} (attempt {attempt+1}/{retries+1})')
                    r = client.get(url, headers=headers)
                    return r.status_code, r.text, str(r.url)
            except Exception as e:
                last_exc = e
                if debug: print(f'[DBG] httpx error on {url}: {e}')
        raise last_exc if last_exc else RuntimeError('httpx error')
    else:
        last_exc = None
        for attempt in range(retries+1):
            try:
                s = requests.Session()
                s.max_redirects = 5
                if debug: print(f'[DBG] GET {url} (attempt {attempt+1}/{retries+1})')
                r = s.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                return r.status_code, r.text, r.url
            except Exception as e:
                last_exc = e
                if debug: print(f'[DBG] requests error on {url}: {e}')
        raise last_exc if last_exc else RuntimeError('requests error')

# ---------------- Parse input ----------------

def parse_input_line(line: str):
    raw = line.strip()
    if not raw:
        raise ValueError("Empty input")
    if "/" in raw:
        net = ipaddress.ip_network(raw, strict=False)
        if not isinstance(net, ipaddress.IPv4Network):
            raise ValueError("Only IPv4 is supported")
        start_ip = ipaddress.IPv4Address(int(net.network_address))
        end_ip = ipaddress.IPv4Address(int(net.broadcast_address))
        return raw, "cidr", start_ip, end_ip, [str(net)]
    if "-" in raw:
        a, b = [x.strip() for x in raw.split("-", 1)]
        start = ipaddress.ip_address(a)
        end = ipaddress.ip_address(b)
        if not (isinstance(start, ipaddress.IPv4Address) and isinstance(end, ipaddress.IPv4Address)):
            raise ValueError("Only IPv4 ranges supported")
        if int(end) < int(start):
            start, end = end, start
        cidrs = [str(c) for c in ipaddress.summarize_address_range(start, end)]
        return raw, "range", start, end, cidrs
    ip = ipaddress.ip_address(raw)
    if not isinstance(ip, ipaddress.IPv4Address):
        raise ValueError("Only IPv4 addresses supported")
    return raw, "single", ip, ip, [str(ip) + "/32"]

# ---------------- RDAP client ----------------

class RDAPClient:
    def __init__(self, user_agent: str = "ip-enricher/1.0", timeout: float = 15.0, retries: int = 2, debug: bool = False):
        self.ua = {"User-Agent": user_agent}
        self.cache: Dict[str, Dict] = {}
        self.timeout = timeout
        self.retries = retries
        self.debug = debug

    def lookup_ip(self, ip: ipaddress.IPv4Address):
        key = f"rdap:{ip.exploded}"
        if key in self.cache:
            doc = self.cache[key]
            return self._parse_rdap(doc)
        url = f"https://rdap.org/ip/{ip.exploded}"
        backoff = 2.0
        for _ in range(5):
            code, text, final = http_get(url, headers=self.ua, timeout=self.timeout, retries=self.retries, debug=self.debug)
            if code == 200:
                try:
                    doc = json.loads(text)
                except Exception:
                    break
                doc["_rdap_final_url"] = final
                self.cache[key] = doc
                return self._parse_rdap(doc)
            elif code in (429, 503):
                if self.debug: print(f"[DBG] RDAP backoff {backoff}s for {ip}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            else:
                break
        return None, None, None, None, None

    def _parse_rdap(self, doc: Dict):
        rdap_url = doc.get("_rdap_final_url")
        registry = None
        if rdap_url:
            from urllib.parse import urlparse
            host = urlparse(rdap_url).netloc.lower()
            if "arin.net" in host:
                registry = "ARIN"
            elif "ripe.net" in host:
                registry = "RIPE NCC"
            elif "apnic.net" in host:
                registry = "APNIC"
            elif "lacnic.net" in host:
                registry = "LACNIC"
            elif "afrinic.net" in host:
                registry = "AFRINIC"
            else:
                registry = host
        handle = doc.get("handle")
        net_type = doc.get("type")
        owner = None
        for ent in doc.get("entities", []):
            roles = ent.get("roles", [])
            if any(r in roles for r in ("registrant", "administrative", "technical", "abuse", "noc", "organization")):
                v = ent.get("vcardArray")
                if isinstance(v, list) and len(v) == 2 and isinstance(v[1], list):
                    for item in v[1]:
                        try:
                            if item[0] == "fn":
                                owner = item[3]
                                break
                        except Exception:
                            pass
                if owner:
                    break
        if not owner:
            owner = doc.get("name")
        return owner, handle, net_type, registry, rdap_url

# ---------------- AWS ranges ----------------

class AWSRanges:
    def __init__(self, timeout: float = 15.0, retries: int = 2, debug: bool = False):
        self.loaded = False
        self.timeout = timeout
        self.retries = retries
        self.debug = debug
        self.prefixes_v4: List[Tuple[ipaddress.IPv4Network, str, str]] = []

    def ensure_loaded(self):
        if self.loaded:
            return
        url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
        code, text, _ = http_get(url, timeout=self.timeout, retries=self.retries, debug=self.debug)
        if code == 200:
            data = json.loads(text)
            for p in data.get("prefixes", []):
                try:
                    net = ipaddress.ip_network(p.get("ip_prefix"))
                    if isinstance(net, ipaddress.IPv4Network):
                        self.prefixes_v4.append((net, p.get("service", "AMAZON"), p.get("region", "GLOBAL")))
                except Exception:
                    continue
            self.loaded = True

    def match(self, ips_or_nets: List[ipaddress._BaseNetwork | ipaddress.IPv4Address]):
        self.ensure_loaded()
        if not self.loaded:
            return False, [], []
        services, regions = set(), set()
        matched = False
        for cand in ips_or_nets:
            cnet = ipaddress.ip_network(str(cand) + "/32") if isinstance(cand, ipaddress.IPv4Address) else cand
            for net, svc, reg in self.prefixes_v4:
                if cnet.overlaps(net):
                    matched = True
                    services.add(svc)
                    regions.add(reg)
        return matched, sorted(services), sorted(regions)

# ---------------- WHOIS (port 43) ----------------

RIR_WHOIS = {
    'ARIN': 'whois.arin.net',
    'RIPE NCC': 'whois.ripe.net',
    'APNIC': 'whois.apnic.net',
    'LACNIC': 'whois.lacnic.net',
    'AFRINIC': 'whois.afrinic.net',
}

def whois_query(ip: str, registry_hint: Optional[str], timeout: float = 10.0, debug: bool = False) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (org, asn, raw_path) best-effort by querying the RIR WHOIS server.
       raw_path is "rir:server" string for traceability.
    """
    server = None
    if registry_hint and registry_hint in RIR_WHOIS:
        server = RIR_WHOIS[registry_hint]
    else:
        # Default to ARIN bootstrap if unknown
        server = 'whois.arin.net'
    raw = None
    try:
        if debug: print(f"[DBG] WHOIS {ip} via {server}")
        with socket.create_connection((server, 43), timeout=timeout) as sock:
            # Send the IP + CRLF
            q = (ip + "\r\n").encode('ascii', errors='ignore')
            sock.sendall(q)
            chunks = []
            sock.settimeout(timeout)
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                chunks.append(data)
        raw = b''.join(chunks).decode('utf-8', errors='ignore')
    except Exception as e:
        if debug: print(f"[DBG] WHOIS error: {e}")
        return None, None, f"{registry_hint or 'UNKNOWN'}:{server}"

    # Best-effort parse across RIR formats
    org = None
    asn = None
    # Common fields
    patterns = [
        r"^OrgName:\s*(.+)$",            # ARIN
        r"^org-name:\s*(.+)$",           # RIPE
        r"^owner:\s*(.+)$",              # LACNIC
        r"^responsible:\s*(.+)$",        # LACNIC alt
        r"^descr:\s*(.+)$",              # many
    ]
    for line in raw.splitlines():
        l = line.strip()
        for pat in patterns:
            m = re.match(pat, l, flags=re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                # Prefer a more specific owner/org; accept first strong hit
                if org is None or pat.lower() in ("^orgname:", "^org-name:"):
                    org = val
                break
        # ASN often appears as 'origin: ASXXXX' in RIPE/APNIC/LACNIC, or 'originAS' in ARIN remarks
        m_as = re.match(r"^(origin|originas|origin-as)\s*:\s*(AS\d+)\b", l, flags=re.IGNORECASE)
        if m_as:
            asn = m_as.group(2).upper()
    return org, asn, f"{registry_hint or 'UNKNOWN'}:{server}"

# ---------------- File input ----------------

def iter_inputs(path: str) -> List[str]:
    items: List[str] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        head = f.read(4096)
        f.seek(0)
        if "," in head and "input" in head.splitlines()[0].lower():
            reader = csv.DictReader(f)
            for row in reader:
                v = (row.get("input") or "").strip()
                if v:
                    items.append(v)
        else:
            for line in f:
                v = line.strip()
                if v:
                    items.append(v)
    return items

# ---------------- Main ----------------

def main():
    ap = argparse.ArgumentParser(description="Enrich IPs with RDAP owner, AWS, and WHOIS (no IPinfo needed).")
    ap.add_argument("--in", dest="inp", required=True, help="Path to input file (TXT or CSV with 'input' column)")
    ap.add_argument("--out", dest="outp", required=True, help="Output CSV path")
    ap.add_argument("--aws", action="store_true", help="Include AWS ip-ranges.json mapping")
    ap.add_argument("--debug", action="store_true", help="Verbose debug logging")
    ap.add_argument("--timeout", dest="timeout", type=float, default=15.0, help="HTTP/WHOIS timeout (seconds)")
    ap.add_argument("--retries", dest="retries", type=int, default=2, help="HTTP retries on errors (not including RDAP 429/503 backoff)")
    ap.add_argument("--no-whois", action="store_true", help="Skip WHOIS (only RDAP/AWS)")
    args = ap.parse_args()

    rows_in = iter_inputs(args.inp)
    if not rows_in:
        print("No inputs found.")
        sys.exit(2)

    rdap = RDAPClient(timeout=args.timeout, retries=args.retries, debug=args.debug)
    aws = AWSRanges(timeout=args.timeout, retries=args.retries, debug=args.debug) if args.aws else None

    out_fields = [
        "input","type","start_ip","end_ip","cidr_list",
        "rir_owner","rir_handle","rir_type","rir_registry","rdap_url",
        "aws_match","aws_services","aws_regions",
        "whois_org","whois_asn","whois_raw_path",
    ]

    with open(args.outp, "w", newline="", encoding="utf-8") as fo:
        w = csv.DictWriter(fo, fieldnames=out_fields)
        w.writeheader()
        for item in rows_in:
            try:
                raw, typ, start_ip, end_ip, cidrs = parse_input_line(item)
            except Exception as e:
                print(f"[WARN] Skipping '{item}': {e}", file=sys.stderr)
                continue

            rep_ip = start_ip

            # RDAP authoritative owner/registry
            owner, handle, net_type, registry, rdap_url = rdap.lookup_ip(rep_ip)

            # AWS mapping
            aws_match = False
            aws_services: List[str] = []
            aws_regions: List[str] = []
            if aws is not None:
                cand_networks: List[ipaddress.IPv4Network] = []
                for c in cidrs:
                    try:
                        cand_networks.append(ipaddress.ip_network(c, strict=False))
                    except Exception:
                        pass
                matched, svcs, regs = aws.match(cand_networks + [rep_ip])
                aws_match, aws_services, aws_regions = matched, svcs, regs

            # WHOIS enrichment (best-effort)
            whois_org = whois_asn = whois_raw_path = None
            if not args.no_whois:
                whois_org, whois_asn, whois_raw_path = whois_query(rep_ip.exploded, registry, timeout=args.timeout, debug=args.debug)

            w.writerow({
                "input": raw,
                "type": typ,
                "start_ip": str(start_ip),
                "end_ip": str(end_ip),
                "cidr_list": " ".join(cidrs),
                "rir_owner": owner or "",
                "rir_handle": handle or "",
                "rir_type": net_type or "",
                "rir_registry": registry or "",
                "rdap_url": rdap_url or "",
                "aws_match": str(aws_match).lower() if aws is not None else "",
                "aws_services": ",".join(aws_services) if aws is not None else "",
                "aws_regions": ",".join(aws_regions) if aws is not None else "",
                "whois_org": whois_org or "",
                "whois_asn": whois_asn or "",
                "whois_raw_path": whois_raw_path or "",
            })

    print(f"Done. Wrote {args.outp}")

if __name__ == "__main__":
    main()
