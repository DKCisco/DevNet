import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import csv
import random
import sys
import os

# --- Data Loading Function ---
def load_questions_from_csv(filename="quiz_questions.csv"):
    """
    Loads quiz questions from a specified CSV file.
    Returns a list of question dictionaries, or None if a critical error occurs.
    """
    if not os.path.exists(filename):
        messagebox.showerror("Error", f"The file '{filename}' was not found.")
        return None
        
    quiz_data = []
    try:
        with open(filename, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)

            required_cols = ['question', 'correct_answer', 'explanation']
            if not all(col in header for col in required_cols):
                messagebox.showerror("CSV Error", "CSV file is missing one of the required columns: 'question', 'correct_answer', 'explanation'.")
                return None

            question_idx = header.index('question')
            option_cols = [f'option_{chr(97 + i)}' for i in range(6)]
            option_indices = [header.index(col) for col in option_cols if col in header]
            answer_idx = header.index('correct_answer')
            explanation_idx = header.index('explanation')

            for row in reader:
                options = [row[i] for i in option_indices if row[i]]
                correct_answer_text = row[answer_idx]
                
                if row[question_idx] and options and correct_answer_text:
                    try:
                        answer_index = options.index(correct_answer_text)
                        quiz_data.append({
                            'question': row[question_idx],
                            'options': options,
                            'answer_index': answer_index,
                            'explanation': row[explanation_idx]
                        })
                    except ValueError:
                        pass # Silently skip rows where the answer isn't in the options
    except Exception as e:
        messagebox.showerror("File Error", f"An error occurred while reading the CSV file: {e}")
        return None
        
    return quiz_data

# --- Main Application Class ---
class QuizApp:
    def __init__(self, root, quiz_data):
        self.root = root
        self.all_questions = quiz_data
        self.questions_to_ask = []
        
        # State variables
        self.current_question_index = 0
        self.score = 0
        self.selected_option = tk.IntVar()

        # Configure main window
        self.root.title("Network Quiz")
        self.root.geometry("800x600")
        self.root.config(bg="#f0f0f0")

        # Style configuration
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 12))
        self.style.configure("Header.TLabel", font=("Helvetica", 18, "bold"))
        self.style.configure("Question.TLabel", font=("Helvetica", 14, "bold"))
        self.style.configure("TButton", font=("Helvetica", 12, "bold"), padding=10)
        self.style.configure("TRadiobutton", background="#f0f0f0", font=("Helvetica", 12))

        self.setup_start_screen()

    def clear_frame(self):
        """Removes all widgets from the root window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def setup_start_screen(self):
        """Displays the initial screen to start the quiz."""
        self.clear_frame()
        self.current_question_index = 0
        self.score = 0

        start_frame = ttk.Frame(self.root, padding="20")
        start_frame.pack(expand=True, fill="both")

        ttk.Label(start_frame, text="Welcome to the Network Quiz!", style="Header.TLabel").pack(pady=20)
        ttk.Label(start_frame, text="This is study mode. You'll get immediate feedback.").pack(pady=10)

        # Frame for question count selection
        input_frame = ttk.Frame(start_frame)
        input_frame.pack(pady=20)
        
        ttk.Label(input_frame, text=f"How many questions? (1-{len(self.all_questions)}):").pack(side="left", padx=5)
        
        self.num_questions_entry = ttk.Entry(input_frame, width=5)
        self.num_questions_entry.pack(side="left")
        
        start_button = ttk.Button(start_frame, text="Start Quiz", command=self.start_quiz)
        start_button.pack(pady=20)

    def start_quiz(self):
        """Validates input and begins the quiz."""
        try:
            num = int(self.num_questions_entry.get())
            if not (1 <= num <= len(self.all_questions)):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", f"Please enter a number between 1 and {len(self.all_questions)}.")
            return

        # Shuffle and select the questions for this session
        randomized = self.all_questions.copy()
        random.shuffle(randomized)
        self.questions_to_ask = randomized[:num]
        
        self.display_question()

    def display_question(self):
        """Clears the frame and shows the current question."""
        self.clear_frame()
        self.selected_option.set(-1) # Reset selection

        q_data = self.questions_to_ask[self.current_question_index]

        quiz_frame = ttk.Frame(self.root, padding="20")
        quiz_frame.pack(expand=True, fill="both")

        # Question Number Header
        header_text = f"Question {self.current_question_index + 1} of {len(self.questions_to_ask)}"
        ttk.Label(quiz_frame, text=header_text, style="Header.TLabel").pack(pady=10, anchor="w")
        
        # Question Text
        question_label = ttk.Label(quiz_frame, text=q_data['question'], style="Question.TLabel", wraplength=750)
        question_label.pack(pady=20, anchor="w")

        # Options
        options_frame = ttk.Frame(quiz_frame)
        options_frame.pack(fill="x", pady=10)
        
        for i, option in enumerate(q_data['options']):
            rb = ttk.Radiobutton(options_frame, text=option, variable=self.selected_option, value=i, style="TRadiobutton")
            rb.pack(anchor="w", pady=5)

        # Submit Button
        submit_button = ttk.Button(quiz_frame, text="Submit Answer", command=self.check_answer)
        submit_button.pack(pady=30)

    def check_answer(self):
        """Checks the selected answer and shows feedback."""
        if self.selected_option.get() == -1:
            messagebox.showwarning("No Selection", "Please select an answer.")
            return

        q_data = self.questions_to_ask[self.current_question_index]
        user_answer_index = self.selected_option.get()
        correct_answer_index = q_data['answer_index']

        is_correct = (user_answer_index == correct_answer_index)
        if is_correct:
            self.score += 1
        
        self.show_feedback(is_correct, q_data)

    def show_feedback(self, is_correct, q_data):
        """Displays a feedback window with the explanation."""
        feedback_win = tk.Toplevel(self.root)
        feedback_win.title("Result")
        feedback_win.geometry("600x400")
        
        feedback_frame = ttk.Frame(feedback_win, padding="20")
        feedback_frame.pack(expand=True, fill="both")

        if is_correct:
            result_text = "Correct!"
            color = "green"
        else:
            correct_option_text = q_data['options'][q_data['answer_index']]
            result_text = f"Incorrect. The correct answer was:\n\n'{correct_option_text}'"
            color = "red"

        ttk.Label(feedback_frame, text=result_text, font=("Helvetica", 16, "bold"), foreground=color).pack(pady=10)
        
        ttk.Label(feedback_frame, text="Explanation:", font=("Helvetica", 12, "bold")).pack(pady=(20, 5), anchor="w")
        
        explanation_label = ttk.Label(feedback_frame, text=q_data['explanation'], wraplength=550)
        explanation_label.pack(pady=5, anchor="w")

        next_button = ttk.Button(feedback_frame, text="Next", command=lambda: self.next_question(feedback_win))
        next_button.pack(pady=20)
        
        # Make the feedback window modal
        feedback_win.transient(self.root)
        feedback_win.grab_set()
        self.root.wait_window(feedback_win)

    def next_question(self, feedback_window):
        """Closes the feedback window and moves to the next question or results."""
        feedback_window.destroy()
        self.current_question_index += 1
        if self.current_question_index < len(self.questions_to_ask):
            self.display_question()
        else:
            self.show_final_results()

    def show_final_results(self):
        """Displays the final score."""
        self.clear_frame()
        
        results_frame = ttk.Frame(self.root, padding="20")
        results_frame.pack(expand=True, fill="both")

        ttk.Label(results_frame, text="Quiz Complete!", style="Header.TLabel").pack(pady=20)
        
        total = len(self.questions_to_ask)
        percentage = (self.score / total) * 100 if total > 0 else 0
        
        score_text = f"Your Final Score: {self.score} / {total} ({percentage:.2f}%)"
        ttk.Label(results_frame, text=score_text, font=("Helvetica", 16)).pack(pady=20)

        restart_button = ttk.Button(results_frame, text="Try Again", command=self.setup_start_screen)
        restart_button.pack(pady=20)


# --- Script Execution ---
if __name__ == "__main__":
    # Load questions from the CSV file first
    quiz_data_from_file = load_questions_from_csv()
    
    if quiz_data_from_file is None or not quiz_data_from_file:
        # Error messages are handled inside the loading function
        sys.exit(1)
        
    # Create and run the Tkinter application
    main_window = tk.Tk()
    app = QuizApp(main_window, quiz_data_from_file)
    main_window.mainloop()
