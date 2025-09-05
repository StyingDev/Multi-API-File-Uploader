import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os

class FileUploaderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Multi-API File Uploader")
        self.master.geometry("800x600")

        # API settings
        self.apis = {
            "Uguu (64MB)": {
                "url": "https://uguu.se/upload",
                "file_field": "files[]",
                "limit_mb": 64,
                "unlimited": False,
                "response_field": "files",
                "url_field": "0.url",
            },
            "TMP/FILES": {
                "url": "https://tmpfiles.org/api/v1/upload", 
                "file_field": "file", 
                "limit_mb": None, 
                "unlimited": True, 
                "response_field": "data", 
                "url_field": "url"
            },
            "AnonymFile (5GB)": {
                "url": "https://anonymfile.com/api/v1/upload",
                "file_field": "file",
                "limit_mb": 5000,
                "unlimited": False,
                "response_field": "data",
                "url_field": "file.url.full",
            },
            "ShareFile (5GB)": {
                "url": "https://sharefile.co/api/v1/upload",
                "file_field": "file",
                "limit_mb": 5000,
                "unlimited": False,
                "response_field": "data",
                "url_field": "file.url.full",
            },
            "GoFile (5GB)": {
                "url": "https://gofile.to/api/v1/upload",
                "file_field": "file",
                "limit_mb": 5000,
                "unlimited": False,
                "response_field": "data",
                "url_field": "file.url.full",
            }
        }


        self.current_api = tk.StringVar(value="Uguu")
        self.uploaded_urls = []

        self.create_ui()

    def create_ui(self):
        top_frame = ttk.Frame(self.master, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Select API:").pack(side=tk.LEFT, padx=5)
        
        self.api_menu = ttk.OptionMenu(top_frame, self.current_api, "Uguu", *self.apis.keys())
        self.api_menu.pack(side=tk.LEFT, padx=5)

        ttk.Button(top_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Upload Files", command=self.upload_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Clear Files", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Clear URLs", command=self.clear_urls).pack(side=tk.LEFT, padx=5)

        file_frame = ttk.LabelFrame(self.master, text="Files to Upload", padding=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.MULTIPLE, height=10)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        url_frame = ttk.LabelFrame(self.master, text="Uploaded File URLs", padding=10)
        url_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.url_listbox = tk.Listbox(url_frame, height=10)
        self.url_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(url_frame, text="Copy Selected URL", command=self.copy_url).pack(pady=5)

    def add_files(self):
        files = filedialog.askopenfilenames()
        for file in files:
            self.file_listbox.insert(tk.END, file)

    def upload_files(self):
        selected_files = [self.file_listbox.get(idx) for idx in self.file_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("No Files Selected", "Please select files to upload.")
            return

        api_name = self.current_api.get()
        api_config = self.apis[api_name]

        # Check size limits
        for file in selected_files:
            file_size_mb = os.path.getsize(file) / (1024 * 1024)
            if not api_config["unlimited"] and file_size_mb > api_config["limit_mb"]:
                messagebox.showerror("File Too Large", f"{file} exceeds the {api_config['limit_mb']} MB limit.")
                return

        for file in selected_files:
            self.upload_file(file, api_config)

    def upload_file(self, file, api_config):
        """
        Upload a file using the selected API configuration.
        """
        url = api_config["url"]
        files = {api_config["file_field"]: open(file, "rb")}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()

            response_data = response.json()
            response_field = api_config["response_field"]
            url_field = api_config["url_field"]

            if response_field in response_data:
                data = response_data[response_field]

                url_parts = url_field.split(".")
                url = data
                for part in url_parts:
                    if isinstance(url, list):
                        part = int(part)
                    url = url[part] if part in url or isinstance(url, list) else None
                    if url is None:
                        break

                if url:
                    self.uploaded_urls.append(url)
                    self.url_listbox.insert(tk.END, f"{os.path.basename(file)} - {url}")
                    messagebox.showinfo("Upload Successful", f"File uploaded: {url}")
                else:
                    messagebox.showwarning("URL Missing", f"File uploaded, but no URL found.\nResponse: {response_data}")
            else:
                messagebox.showerror("Upload Failed", f"Unexpected response format.\nResponse: {response_data}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Upload Error", f"Failed to upload {file}.\nError: {e}")
        finally:
            files[api_config["file_field"]].close()



    def copy_url(self):
        selected_indices = self.url_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No URL Selected", "Please select a URL to copy.")
            return

        urls = [self.url_listbox.get(idx) for idx in selected_indices]
        self.master.clipboard_clear()
        self.master.clipboard_append("\n".join(urls))
        self.master.update()
        messagebox.showinfo("Copied", "Selected URL(s) copied to clipboard.")

    def clear_files(self):
        self.file_listbox.delete(0, tk.END)

    def clear_urls(self):
        self.url_listbox.delete(0, tk.END)

    def add_api(self, name, url, limit_mb, unlimited, file_field, response_field, url_field):
        """Add a new API to the uploader."""
        self.apis[name] = {
            "url": url,
            "file_field": file_field,
            "limit_mb": limit_mb,
            "unlimited": unlimited,
            "response_field": response_field,
            "url_field": url_field,
        }
        self.update_api_menu()

    def update_api_menu(self):
        """Force the OptionMenu to refresh and show the updated list of APIs."""
        menu = self.master.children["!optionmenu"].children["menu"]
        menu.delete(0, "end")
        for api in self.apis.keys():
            menu.add_command(label=api, command=lambda api=api: self.current_api.set(api))

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = FileUploaderApp(root)
    root.mainloop()
