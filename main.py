import subprocess
import sys
from tkinter import messagebox

import customtkinter as ctk
import requests

from inventory_dashboard import start_dashboard

# Assuming this file is in the same directory


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Superior Inventory Manager - Security Layer")
        self.geometry("400x500")

        self.backend_process = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # COMMENTED OUT: This machine (.123) is a client.
        # The backend should be running manually on the server machine (.252).
        # self.start_backend_thread()

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.show_login_screen()

    # def start_backend_thread(self):
    #     """Starts the uvicorn server in a separate thread and tracks the process."""
    #
    #     def run_server():
    #         # Find the path for server.py
    #         base_path = getattr(
    #             sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
    #         )
    #
    #         # Start the backend silently
    #         self.backend_process = subprocess.Popen(
    #             [
    #                 sys.executable,
    #                 "-m",
    #                 "uvicorn",
    #                 "server:app",
    #                 "--port",
    #                 "8000", # Fixed port argument order
    #                 "--host",
    #                 "0.0.0.0",
    #             ],
    #             cwd=base_path,
    #             creationflags=0x08000000,  # CREATE_NO_WINDOW
    #         )
    #
    #     threading.Thread(target=run_server, daemon=True).start()

    def on_closing(self):
        """Cleanly kills the backend process tree and exits."""
        if hasattr(self, "backend_process") and self.backend_process:
            try:
                # Force kill the process and its children silently
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.backend_process.pid)],
                    capture_output=True,
                    creationflags=0x08000000,
                )
            except Exception as e:
                print(f"Cleanup error: {e}")

        self.destroy()
        sys.exit()

    def clear_container(self):
        """Clears the screen before loading a new one."""
        for child in self.container.winfo_children():
            child.destroy()

    # ================= LOGIN SCREEN =================
    def show_login_screen(self):
        self.clear_container()
        frame = ctk.CTkFrame(self.container)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="Welcome Back", font=("Arial", 24, "bold")).pack(
            pady=20
        )

        self.u_login = ctk.CTkEntry(frame, placeholder_text="Username", width=250)
        self.u_login.pack(pady=10)

        self.p_login = ctk.CTkEntry(
            frame, placeholder_text="Password", show="*", width=250
        )
        self.p_login.pack(pady=10)

        ctk.CTkButton(frame, text="Login", command=self.process_login, width=250).pack(
            pady=10
        )
        ctk.CTkButton(
            frame,
            text="Create Account",
            fg_color="transparent",
            border_width=1,
            command=self.show_register_screen,
        ).pack(pady=10)

    # ================= REGISTRATION SCREEN =================
    def show_register_screen(self):
        self.clear_container()
        frame = ctk.CTkFrame(self.container)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="Register New Account", font=("Arial", 22)).pack(
            pady=20
        )

        self.reg_user = ctk.CTkEntry(frame, placeholder_text="Username", width=250)
        self.reg_user.pack(pady=5)
        self.reg_email = ctk.CTkEntry(frame, placeholder_text="Email", width=250)
        self.reg_email.pack(pady=5)
        self.reg_pass = ctk.CTkEntry(
            frame, placeholder_text="Password", show="*", width=250
        )
        self.reg_pass.pack(pady=5)

        ctk.CTkButton(frame, text="Sign Up", command=self.process_registration).pack(
            pady=10
        )
        ctk.CTkButton(
            frame,
            text="Back to Login",
            fg_color="transparent",
            command=self.show_login_screen,
        ).pack()

    # ================= LOGIC METHODS =================
    def process_login(self):
        username = self.u_login.get().strip()
        password = self.p_login.get().strip()

        if not username or not password:
            messagebox.showwarning(
                "Input Error", "Please enter both username and password"
            )
            return

        payload = {"username": username, "password": password}

        try:
            # Pointing to the .252 server machine
            response = requests.post("http://192.168.200.252:8000/login", json=payload)

            if response.status_code == 200:
                data = response.json()
                user_info = {
                    "id": data.get("id"),
                    "username": data.get("username"),
                    "token": data.get("access_token"),
                    "role": data.get("role"),
                    "role_id": data.get("role_id"),
                }

                messagebox.showinfo(
                    "Success", f"Welcome back, {user_info['username']}!"
                )
                self.transition_to_dashboard(user_info)
            elif response.status_code == 401:
                messagebox.showerror("Login Failed", "Invalid username or password.")
            else:
                detail = response.json().get("detail", "An unknown error occurred.")
                messagebox.showerror(
                    "Server Error", f"Error {response.status_code}: {detail}"
                )

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                "Could not connect to FastAPI server at 192.168.200.252:8000. Is it running?",
            )
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def process_registration(self):
        username = self.reg_user.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_pass.get().strip()

        if not username or not email or not password:
            messagebox.showwarning("Input Error", "All fields are required!")
            return

        payload = {"username": username, "email": email, "password": password}

        try:
            response = requests.post(
                "http://192.168.200.252:8000/register", json=payload
            )

            if response.status_code in [200, 201]:
                messagebox.showinfo("Success", "Account created! Please log in.")
                self.show_login_screen()
            else:
                detail = response.json().get("detail", "Registration failed.")
                messagebox.showerror("Registration Failed", detail)

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                "FastAPI server is not reachable on 192.168.200.252:8000.",
            )
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def transition_to_dashboard(self, user_data):
        self.clear_container()
        self.geometry("1100x750")
        start_dashboard(self.container, user_data)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
