import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Connect to SQLite database
conn = sqlite3.connect("movie_booking.db")
cursor = conn.cursor()

# Create tables if not exist
cursor.executescript("""
CREATE TABLE IF NOT EXISTS Movies (
    MovieID INTEGER PRIMARY KEY AUTOINCREMENT,
    Title TEXT,
    Genre TEXT,
    Duration INTEGER,
    Rating REAL
);

CREATE TABLE IF NOT EXISTS Theaters (
    TheaterID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    Location TEXT
);

CREATE TABLE IF NOT EXISTS Shows (
    ShowID INTEGER PRIMARY KEY AUTOINCREMENT,
    MovieID INTEGER,
    TheaterID INTEGER,
    ShowTime TEXT,
    AvailableSeats INTEGER,
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID),
    FOREIGN KEY (TheaterID) REFERENCES Theaters(TheaterID)
);

CREATE TABLE IF NOT EXISTS Customers (
    CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    Email TEXT,
    Phone TEXT
);

CREATE TABLE IF NOT EXISTS Bookings (
    BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
    ShowID INTEGER,
    CustomerID INTEGER,
    SeatsBooked INTEGER,
    BookingTime TEXT,
    FOREIGN KEY (ShowID) REFERENCES Shows(ShowID),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);
""")
conn.commit()

# Insert sample data
def insert_sample_data():
    movies = [
        ("Retro", "Action", 136, 8.7),
        ("Mufasa", "Animated", 148, 8.8),
        ("Pushpa 2", "Action", 195, 7.8)
    ]
    for movie in movies:
        cursor.execute("INSERT OR IGNORE INTO Movies (Title, Genre, Duration, Rating) VALUES (?, ?, ?, ?)", movie)

    theaters = [
        ("PVR", "Chennai"),
        ("Marina Mall", "Navalur")
    ]
    for theater in theaters:
        cursor.execute("INSERT OR IGNORE INTO Theaters (Name, Location) VALUES (?, ?)", theater)

    shows = [
        (1, 1, "10:00 AM", 50),
        (2, 2, "12:00 PM", 40),
        (3, 1, "02:00 PM", 30)
    ]
    for show in shows:
        cursor.execute("INSERT OR IGNORE INTO Shows (MovieID, TheaterID, ShowTime, AvailableSeats) VALUES (?, ?, ?, ?)", show)

    conn.commit()

insert_sample_data()

# GUI setup
root = tk.Tk()
root.title("Movie Ticket Booking System")
root.geometry("600x400")

def view_movies():
    win = tk.Toplevel(root)
    win.title("Available Movies")
    tree = ttk.Treeview(win, columns=("Title", "Genre", "Duration", "Rating"), show="headings")
    tree.heading("Title", text="Title")
    tree.heading("Genre", text="Genre")
    tree.heading("Duration", text="Duration")
    tree.heading("Rating", text="Rating")
    tree.pack(fill=tk.BOTH, expand=True)

    cursor.execute("SELECT Title, Genre, Duration, Rating FROM Movies")
    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)

def view_shows():
    win = tk.Toplevel(root)
    win.title("Available Shows")
    tree = ttk.Treeview(win, columns=("Title", "Theater", "Time", "Seats"), show="headings")
    tree.heading("Title", text="Movie")
    tree.heading("Theater", text="Theater")
    tree.heading("Time", text="Show Time")
    tree.heading("Seats", text="Available Seats")
    tree.pack(fill=tk.BOTH, expand=True)

    cursor.execute("""
        SELECT m.Title, t.Name, s.ShowTime, s.AvailableSeats
        FROM Shows s
        JOIN Movies m ON s.MovieID = m.MovieID
        JOIN Theaters t ON s.TheaterID = t.TheaterID
    """)
    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)

def book_ticket():
    def confirm_booking():
        name = entry_name.get()
        email = entry_email.get()
        phone = entry_phone.get()
        show_id = int(entry_show_id.get())
        seats = int(entry_seats.get())

        cursor.execute("SELECT AvailableSeats FROM Shows WHERE ShowID = ?", (show_id,))
        available = cursor.fetchone()
        if available and available[0] >= seats:
            cursor.execute("INSERT INTO Customers (Name, Email, Phone) VALUES (?, ?, ?)", (name, email, phone))
            customer_id = cursor.lastrowid
            booking_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO Bookings (ShowID, CustomerID, SeatsBooked, BookingTime) VALUES (?, ?, ?, ?)",
                           (show_id, customer_id, seats, booking_time))
            cursor.execute("UPDATE Shows SET AvailableSeats = AvailableSeats - ? WHERE ShowID = ?", (seats, show_id))
            conn.commit()
            messagebox.showinfo("Success", "Booking successful!")
            book.destroy()
        else:
            messagebox.showerror("Error", "Not enough seats available.")

    book = tk.Toplevel(root)
    book.title("Book Ticket")

    tk.Label(book, text="Name").pack()
    entry_name = tk.Entry(book)
    entry_name.pack()

    tk.Label(book, text="Email").pack()
    entry_email = tk.Entry(book)
    entry_email.pack()

    tk.Label(book, text="Phone").pack()
    entry_phone = tk.Entry(book)
    entry_phone.pack()

    tk.Label(book, text="Show ID").pack()
    entry_show_id = tk.Entry(book)
    entry_show_id.pack()

    tk.Label(book, text="Seats").pack()
    entry_seats = tk.Entry(book)
    entry_seats.pack()

    tk.Button(book, text="Confirm", command=confirm_booking).pack(pady=10)

def view_bookings():
    win = tk.Toplevel(root)
    win.title("All Bookings")
    tree = ttk.Treeview(win, columns=("Customer", "Movie", "Time", "Seats"), show="headings")
    tree.heading("Customer", text="Customer")
    tree.heading("Movie", text="Movie")
    tree.heading("Time", text="Show Time")
    tree.heading("Seats", text="Seats Booked")
    tree.pack(fill=tk.BOTH, expand=True)

    cursor.execute("""
        SELECT c.Name, m.Title, s.ShowTime, b.SeatsBooked
        FROM Bookings b
        JOIN Customers c ON b.CustomerID = c.CustomerID
        JOIN Shows s ON b.ShowID = s.ShowID
        JOIN Movies m ON s.MovieID = m.MovieID
    """)
    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)

def search_movie():
    def do_search():
        title = entry_search.get()
        cursor.execute("SELECT Title, Genre, Duration, Rating FROM Movies WHERE Title LIKE ?", ('%' + title + '%',))
        results = cursor.fetchall()
        if results:
            for row in tree.get_children():
                tree.delete(row)
            for movie in results:
                tree.insert("", tk.END, values=movie)
        else:
            messagebox.showinfo("Info", "No movies found.")

    win = tk.Toplevel(root)
    win.title("Search Movie")
    tk.Label(win, text="Enter movie title:").pack()
    entry_search = tk.Entry(win)
    entry_search.pack()
    tk.Button(win, text="Search", command=do_search).pack()

    tree = ttk.Treeview(win, columns=("Title", "Genre", "Duration", "Rating"), show="headings")
    tree.heading("Title", text="Title")
    tree.heading("Genre", text="Genre")
    tree.heading("Duration", text="Duration")
    tree.heading("Rating", text="Rating")
    tree.pack(fill=tk.BOTH, expand=True)

def cancel_booking():
    def do_cancel():
        booking_id = entry_id.get()
        cursor.execute("SELECT ShowID, SeatsBooked FROM Bookings WHERE BookingID = ?", (booking_id,))
        booking = cursor.fetchone()
        if booking:
            show_id, seats = booking
            cursor.execute("DELETE FROM Bookings WHERE BookingID = ?", (booking_id,))
            cursor.execute("UPDATE Shows SET AvailableSeats = AvailableSeats + ? WHERE ShowID = ?", (seats, show_id))
            conn.commit()
            messagebox.showinfo("Cancelled", "Booking cancelled.")
            cancel_win.destroy()
        else:
            messagebox.showerror("Error", "Booking ID not found.")

    cancel_win = tk.Toplevel(root)
    cancel_win.title("Cancel Booking")
    tk.Label(cancel_win, text="Enter Booking ID:").pack()
    entry_id = tk.Entry(cancel_win)
    entry_id.pack()
    tk.Button(cancel_win, text="Cancel Booking", command=do_cancel).pack(pady=10)

# Main Menu Buttons
tk.Button(root, text="View Movies", command=view_movies, width=30).pack(pady=5)
tk.Button(root, text="View Shows", command=view_shows, width=30).pack(pady=5)
tk.Button(root, text="Book Ticket", command=book_ticket, width=30).pack(pady=5)
tk.Button(root, text="View Bookings", command=view_bookings, width=30).pack(pady=5)
tk.Button(root, text="Search Movie", command=search_movie, width=30).pack(pady=5)
tk.Button(root, text="Cancel Booking", command=cancel_booking, width=30).pack(pady=5)
tk.Button(root, text="Exit", command=root.destroy, width=30).pack(pady=10)

root.mainloop()