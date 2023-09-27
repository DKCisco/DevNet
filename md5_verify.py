import hashlib

def compute_md5(file_path):
    """Compute the MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)  # read in 64k chunks
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()

def verify_md5(file_path, known_hash):
    """Verify the MD5 hash of a file against a known hash."""
    computed_hash = compute_md5(file_path)
    if computed_hash == known_hash:
        print("Hashes match!")
    else:
        print(f"Hashes do not match!\nComputed: {computed_hash}\nExpected: {known_hash}")

if __name__ == "__main__":
    file_path = input("Enter the path to the file: ")
    known_hash = input("Enter the known MD5 hash: ")
    verify_md5(file_path, known_hash)
