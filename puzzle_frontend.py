import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image, ImageTk
import json

class PuzzleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Rompecabezas - Slide Puzzle")
        
        self.username = None
        self.password = None
        self.puzzle_id = None
        self.grid_size = 3
        self.current_state = None
        self.piece_images = []
        self.grid_buttons = []
        
        self.show_login()
    
    def show_login(self):
        self.login_frame = tk.Frame(self.root, padx=50, pady=50)
        self.login_frame.pack()
        
        tk.Label(self.login_frame, text="LOGIN", font=('Arial', 20, 'bold')).pack(pady=20)
        
        tk.Label(self.login_frame, text="Usuario:").pack()
        self.user_entry = tk.Entry(self.login_frame)
        self.user_entry.pack(pady=5)
        
        tk.Label(self.login_frame, text="Password:").pack()
        self.pass_entry = tk.Entry(self.login_frame, show='*')
        self.pass_entry.pack(pady=5)
        
        tk.Button(self.login_frame, text="Login", command=self.login, 
                  bg='#4CAF50', fg='white', width=15).pack(pady=10)
        tk.Button(self.login_frame, text="Register", command=self.register, 
                  bg='#2196F3', fg='white', width=15).pack(pady=5)
    
    def register(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Completa todos los campos")
            return
        
        response = requests.post('http://localhost:5000/register',
                              json={'username': username, 'password': password})
        
        if response.status_code == 200:
            messagebox.showinfo("Success", "Usuario creado! Ahora haz login")
        else:
            messagebox.showerror("Error", response.json()['error'])
    
    def login(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Completa todos los campos")
            return
        
        response = requests.post('http://localhost:5000/login',
                              json={'username': username, 'password': password})
        
        if response.status_code == 200:
            self.username = username
            self.login_frame.destroy()
            self.show_main_menu()
        else:
            messagebox.showerror("Error", response.json()['error'])
    
    def show_main_menu(self):
        self.menu_frame = tk.Frame(self.root, padx=50, pady=50)
        self.menu_frame.pack()
        
        tk.Label(self.menu_frame, text=f"¡Hola {self.username}!", 
                 font=('Arial', 20, 'bold')).pack(pady=20)
        
        tk.Button(self.menu_frame, text="Nuevo Rompecabezas", 
                  command=self.create_puzzle, bg='#4CAF50', fg='white', 
                  width=25, font=('Arial', 12)).pack(pady=10)
        
        tk.Button(self.menu_frame, text="Ver Mis Rompecabezas", 
                  command=self.show_my_puzzles, bg='#2196F3', fg='white', 
                  width=25, font=('Arial', 12)).pack(pady=10)
        
        tk.Button(self.menu_frame, text="Logout", 
                  command=self.logout, bg='#f44336', fg='white', 
                  width=25, font=('Arial', 12)).pack(pady=10)
    
    def create_puzzle(self):
        self.menu_frame.destroy()
        
        self.puzzle_frame = tk.Frame(self.root, padx=50, pady=50)
        self.puzzle_frame.pack()
        
        tk.Label(self.puzzle_frame, text="Nuevo Rompecabezas", 
                 font=('Arial', 20, 'bold')).pack(pady=20)
        
        tk.Label(self.puzzle_frame, text="Size de cuadrícula (3-5):").pack()
        self.size_entry = tk.Entry(self.puzzle_frame)
        self.size_entry.insert(0, "3")
        self.size_entry.pack(pady=5)
        
        tk.Button(self.puzzle_frame, text="Crear", command=self.start_puzzle, 
                  bg='#4CAF50', fg='white', width=15).pack(pady=10)
    
    def start_puzzle(self):
        try:
            grid_size = int(self.size_entry.get())
            if grid_size < 3 or grid_size > 5:
                messagebox.showerror("Error", "Size debe ser 3, 4 o 5")
                return
        except:
            messagebox.showerror("Error", "Size inválido")
            return
        
        self.grid_size = grid_size
        
        response = requests.post('http://localhost:5000/puzzle/new',
                              json={'grid_size': grid_size, 'image_path': 'puzzle_image.jpg'})
        
        if response.status_code == 200:
            data = response.json()
            self.puzzle_id = data['puzzle_id']
            self.current_state = data['current_state']
            
            self.puzzle_frame.destroy()
            self.show_puzzle_game()
        else:
            messagebox.showerror("Error", response.json()['error'])
    
    def show_puzzle_game(self):
        self.game_frame = tk.Frame(self.root, padx=20, pady=20)
        self.game_frame.pack()
        
        tk.Label(self.game_frame, text="ARMA EL ROMPECABEZAS", 
                 font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Create grid
        self.grid_frame = tk.Frame(self.game_frame)
        self.grid_frame.pack(pady=20)
        
        self.piece_images = []
        self.grid_buttons = []
        
        # Load image and split into pieces
        try:
            image = Image.open('puzzle_image.jpg')
            image = image.resize((400, 400))
            piece_width = 400 // self.grid_size
            piece_height = 400 // self.grid_size
            
            for row in range(self.grid_size):
                button_row = []
                image_row = []
                for col in range(self.grid_size):
                    # Extract piece
                    left = col * piece_width
                    top = row * piece_height
                    right = left + piece_width
                    bottom = top + piece_height
                    
                    piece = image.crop((left, top, right, bottom))
                    photo = ImageTk.PhotoImage(piece)
                    image_row.append(photo)
                    
                    btn = tk.Button(self.grid_frame, image=photo, 
                                  width=piece_width, height=piece_height)
                    btn.row = row
                    btn.col = col
                    btn.config(command=lambda r=row, c=col: self.on_click(r, c))
                    btn.grid(row=row, column=col)
                    button_row.append(btn)
                
                self.grid_buttons.append(button_row)
                self.piece_images.append(image_row)
            
        except Exception as e:
            messagebox.showerror("Error cargar imagen", f"No se encontró puzzle_image.jpg
{e}")
            return
        
        # Control buttons
        tk.Button(self.game_frame, text="Guardar Progreso", 
                  command=self.save_progress, bg='#2196F3', fg='white', 
                  width=15).pack(pady=5)
        
        tk.Button(self.game_frame, text="Cargar Progreso", 
                  command=self.load_progress, bg='#FF9800', fg='white', 
                  width=15).pack(pady=5)
        
        tk.Button(self.game_frame, text="Nuevo Puzzle", 
                  command=self.new_puzzle_from_menu, bg='#4CAF50', fg='white', 
                  width=15).pack(pady=5)
        
        tk.Button(self.game_frame, text="Menú Principal", 
                  command=self.back_to_menu, bg='#f44336', fg='white', 
                  width=15).pack(pady=5)
    
    def on_click(self, row, col):
        if not self.current_state:
            return
        
        # Find where piece (row, col) should go
        current_piece = self.current_state[row][col]
        
        # Find position of this piece in solved state
        target_row = current_piece // self.grid_size
        target_col = current_piece % self.grid_size
        
        # Check if adjacent to target
        if abs(row - target_row) + abs(col - target_col) == 1:
            # Swap
            self.current_state[row][col], self.current_state[target_row][target_col] = \
                self.current_state[target_row][target_col], self.current_state[row][col]
            
            self.update_grid()
            
            # Check if solved
            if self.is_solved():
                messagebox.showinfo("¡Ganaste!", "¡Rompecabezas completado! 🎉")
                self.save_to_db()
    
    def update_grid(self):
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                piece_num = self.current_state[row][col]
                piece_row = piece_num // self.grid_size
                piece_col = piece_num % self.grid_size
                
                self.grid_buttons[row][col].config(image=self.piece_images[piece_row][piece_col])
    
    def is_solved(self):
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.current_state[row][col] != row * self.grid_size + col:
                    return False
        return True
    
    def save_progress(self):
        response = requests.post(f'http://localhost:5000/puzzle/{self.puzzle_id}/save',
                              json={'current_state': self.current_state})
        
        if response.status_code == 200:
            messagebox.showinfo("Success", "Progreso guardado!")
        else:
            messagebox.showerror("Error", response.json()['error'])
    
    def load_progress(self):
        response = requests.get(f'http://localhost:5000/puzzle/{self.puzzle_id}/load')
        
        if response.status_code == 200:
            data = response.json()
            self.current_state = data['current_state']
            self.update_grid()
            messagebox.showinfo("Success", "Progreso cargado!")
        else:
            messagebox.showerror("Error", response.json()['error'])
    
    def new_puzzle_from_menu(self):
        self.update_grid()
        self.game_frame.destroy()
        self.create_puzzle()
    
    def back_to_menu(self):
        self.game_frame.destroy()
        self.show_main_menu()
    
    def show_my_puzzles(self):
        self.menu_frame.destroy()
        
        self.puzzles_frame = tk.Frame(self.root, padx=50, pady=50)
        self.puzzles_frame.pack()
        
        tk.Label(self.puzzles_frame, text="Mis Rompecabezas", 
                 font=('Arial', 20, 'bold')).pack(pady=20)
        
        response = requests.get(f'http://localhost:5000/user/{self.username}/puzzles')
        
        if response.status_code == 200:
            data = response.json()
            puzzles = data['puzzles']
            
            if not puzzles:
                tk.Label(self.puzzles_frame, text="No tienes rompecabezas").pack(pady=20)
            else:
                for puzzle in puzzles:
                    frame = tk.Frame(self.puzzles_frame)
                    frame.pack(pady=5, fill='x')
                    
                    status = puzzle['status']
                    status_text = "✅ Completado" if status == 'completed' else "🔄 En progreso"
                    
                    tk.Label(frame, text=f"Puzzle {puzzle['puzzle_id'][:8]} - Size {puzzle['grid_size']} - {status_text}").pack(side='left')
                    
                    tk.Button(frame, text="Cargar", command=lambda pid=puzzle['puzzle_id']: self.load_puzzle(pid), 
                              width=8).pack(side='right')
        
        tk.Button(self.puzzles_frame, text="Back", command=self.back_to_menu, 
                  width=15).pack(pady=20)
    
    def load_puzzle(self, puzzle_id):
        response = requests.get(f'http://localhost:5000/puzzle/{puzzle_id}/load')
        
        if response.status_code == 200:
            data = response.json()
            self.puzzle_id = puzzle_id
            self.current_state = data['current_state']
            self.grid_size = data['grid_size']
            
            self.puzzles_frame.destroy()
            self.show_puzzle_game()
        else:
            messagebox.showerror("Error", response.json()['error'])
    
    def logout(self):
        response = requests.post('http://localhost:5000/logout')
        self.menu_frame.destroy()
        self.show_login()

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("500x600")
    game = PuzzleGame(root)
    root.mainloop()