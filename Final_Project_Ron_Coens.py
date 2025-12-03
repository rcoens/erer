

# CIS-117 Final Project
#
# Given the URL of an ebook in the Project Gutenburg this script fetches the content of the ebook.
# It then searches the content of the ebook saving the 10 most used words in a database.
# The ten most used words for a book can be queried from the database and displayed.
#
# Author: Ron Coens
# Date: 12/3/2025


import sqlite3
from html.parser import HTMLParser
import urllib
from urllib.request import urlopen
import re
import tkinter as tk
from tkinter import *
from tkinter import messagebox

DATABASE_NAME = 'fp.db'

HEIGHT = 750
WIDTH = 1200

NUM_WORDS_TO_LIST = 10

TITLE_PATTERN = "\*\*\* start of the project gutenberg ebook\s(.*?)(;|\*\*\*)"

EXCLUDED_WORDS = ['mr.', 'an', 'him', '"i','for', 'with', 'but', 'as', 'with', 'on', 'this'
                 'so', 'by','that', 'it', 'his', 'i', 'her', 'a', 'I', 'you', 'he', 'she', 'at', 'in', 'or', 'in', 'to', 'of', 'and', 'the']



class MyHTMLParser(HTMLParser):
    """
    A subclass of HTMLParser that fetches the content of an ebook and
    save the frequency of the words from the ebook in  a dictionary and
    sort the dictionary on the values so the word highest work counts are first.
   """
    
    def __init__(self):
        super().__init__()
        self._counts = []
        self.title = ""


    def handle_data(self, data):
        """
        Called for each block of text between tags.
        count the times a word is found and save the results in self._counts
        """
        counts = {}

        # use an regular expression to find the title of the ebook
        match = re.search(TITLE_PATTERN, data)
        if match:
            #found the title of the book
            self.title = match.group(1).strip()
        
        #search just the book, not text before and after the book text
        start_index = data.find("*** start of the project gutenberg ebook")
        end_index = data.find("*** end of the project gutenberg ebook")
        if start_index != -1 and end_index != -1:
            sub_data = data[start_index+40: end_index]
        else:
            sub_data = data

        # save each word in dictionary with the number of times it is used
        words = sub_data.split()
        for word in words:
            # exclude some words form the count
            if word.lower() not in EXCLUDED_WORDS:
                if word in counts:
                    counts[word] += 1
                else:
                    counts.update({word: 1})

        # sort so highest counr is first
        sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))
        self._counts = sorted_counts


    def collect_counts(self):
        """
        Returns the words and frequenct of the words
        """
        return(self._counts)
      

    def get_title(self):
        """
        Returns the title of the ebook
        """
        return(self.title)



def clear_frame(frame):
    """
    Removes all children in a Tkinter frame

    Parameters
    ----------
    frame : frame object
        The string to present to the user for input.
 
    written by Ronald Coens
    
    """
    for widget in frame.winfo_children():
        widget.destroy()
        

def display_counts(title):
    """
    Fetches the word counts of ebook with title the title from the database
    and display the results.

    Parameters
    ----------
    title : str
        The title of the ebook whose word counts wil be displayed.
 
    written by Ronald Coens
    
    """

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # display the title of the ebook
        ll = tk.Label(title_frame, bg="white", text="Title:  "+title, fg='Blue', font=("Arial", 25))
        ll.place(relx=0.3, rely = 0.5, relheight=1, relwidth=1, anchor = tk.CENTER)

        # create the headers for the columns to be displayed
        e = tk.Entry(results_frame, width=15, fg='Blue', font=('Arial',16,'bold'))
        e.place(relx = 0.0)
        e.grid(row=1, column = 2)
        e.insert(END, ('Word'))
        e = tk.Entry(results_frame, width=15, fg='Blue', font=('Arial',16,'bold'))
        e.grid(row=1, column = 3)
        e.insert(END, ('Count'))

        # query the database for the words and frequency of the words
        cursor.execute("SELECT counts.word, counts.count FROM counts, titles WHERE titles.id = counts.id AND title = ?", (title,))

        # fetch the results from the dababase query and display the results in a grid
        all_rows = cursor.fetchall()
        for i in range(0, len(all_rows)):
            www = all_rows[i]
            for j in range(3):
                if j == 0:
                    ee = tk.Entry(results_frame, width=8,  font=('Arial',16))
                else:
                    ee = tk.Entry(results_frame, width=15,  font=('Arial',16))
                ee.grid(row=i+2, column=j+1)
                if j == 0:
                    ee.insert(END, (i+1))
                else: 
                    ee.insert(END, (www[j-1]))        

        conn.commit()
        cursor.close()
        conn.close()
        
    except sqlite3.Error as e: # Catch all sqlite3-specific errors
        print(f"An SQLite error occurred: {e}")
    finally:
        if conn:
            conn.close()
    

def insert_into_db(title, url, rows):
    
    """
    Insert ebook information into the database.
    First insert the title and url into the titles table.
    Then the word and counts into the counts table

    Parameters
    ----------
    title : str
        The title of the ebook.
    url : str
        The url of the ebook in Project Gutenberg.
    rows : list
        A list of tuples containing the word and count.
 
    written by Ronald Coens
    
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        
        cursor.execute("SELECT id FROM titles WHERE title = ?", (title,))
        title_rrow = cursor.fetchone()
        if not title_rrow:
            # not in table so insert it
                  
            #insert row ito the title table
            cursor.execute("INSERT INTO titles (title, url) VALUES(?,?)", ( title, url))
            #save the tile id
            cursor.execute("SELECT id FROM titles WHERE title = ?", (title,))
            title_row = cursor.fetchone()
            idd = title_row[0]

            #insert rows ito the counts table
            for row in rows:
                word = row[0]
                count = row[1]
                cursor.execute("INSERT INTO counts(id, word, count) VALUES(?,?,?)", (idd, word, count))

        else:
            print("ALREADY in table")
        

        conn.commit()
        cursor.close()
        conn.close()

    except sqlite3.Error as e: # Catch all sqlite3-specific errors
        print(f"An SQLite error occurred: {e}")
    finally:
        if conn:
            conn.close()

            
def parse_page():
    """
    Parses a webpage and returns the frequency of each word on page.

    Returns
    -------
    dictionary
        Each words and the count of each word.
    str
        The title of the ebook.
    str
        The URL of the ebook.

    """
   
    try:
        url  = url_entry.get()
        resp = urlopen(url)
        html = resp.read().decode().lower()

        #parse the webpage
        parser = MyHTMLParser()
        parser.feed(html)

        return (parser.collect_counts(), parser.get_title(), url)

    except ValueError:
        raise ValueError("Invalid URL")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def title_button_clicked():
    """
    Read the user input title. If title is not in the database ask the user to enter a URL.
    If title is in the database display the database entries
    """

    clear_frame(results_frame)
    clear_frame(title_frame)

    # get title from GUI
    title = title_entry.get()
    if not title:
        messagebox.showinfo("", "Enter a title.")
    else:
        try:
            # query database for title
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM titles WHERE title COLLATE NOCASE = ?", (title,))
            
            title_row = cursor.fetchone()
            if not title_row:
                messagebox.showinfo("", "Title not found in databse. Try entering the URL for the book")
            else:
                # title found in DB, display contents
                display_counts(title)
                
            conn.commit()
            cursor.close()
            conn.close()
        except sqlite3.Error as e: # Catch all sqlite3-specific errors
            print(f"An SQLite error occurred: {e}")
        finally:
            title_entry.delete(0, tk.END)
            if conn:
                conn.close()
    

def url_button_clicked():
    """
    Read the user input URL. Call parse_page to get the title and word counts.
    Then insert into the dababase the tile and top ten word counts.
    """
    
    clear_frame(results_frame)
    clear_frame(title_frame)

    if not url_entry.get():
        messagebox.showinfo("", "Enter a URL.")
    else:
        try:
            counts, title, url = parse_page()
            
            if title:
                # found an ebook
                num_words = len(counts)
                if num_words == 0:
                    messagebox.showinfo("", "No words found.")
                else:
                    if num_words > NUM_WORDS_TO_LIST:
                        num_words = NUM_WORDS_TO_LIST

                    # create a  list of the top ten word most frequently used.
                    counts_list = []
                    for i in range(num_words):
                        key = list(counts.keys())[i]
                        value = counts[key]
                        counts_list.append((key, value))

                    # insert the tile and word count into the database
                    insert_into_db(title, url, counts_list)
                    # display the word counts for the ebook
                    display_counts(title)
                        
            else:
                messagebox.showerror("", "No book was found.")


        except ValueError:
            messagebox.showwarning("", "Invalid URL.")
        except urllib.error.URLError:
            messagebox.showwarning("", "Invalid URL.")
        except urllib.error.HTTPError:
            messagebox.showwarning("", "Invalid URL.")
        finally:
            url_entry.delete(0, tk.END)


        

if __name__ == '__main__':


    # create DB tables
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT
                )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS counts (
                id INT,
                word TEXT,
                count INT,
                FOREIGN KEY (id) REFERENCES titles (id)
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()

    except sqlite3.Error as e: # Catch all sqlite3-specific errors
        print(f"An SQLite error occurred: {e}")
    finally:
        if conn:
            conn.close()



    #Set up the tkinter GUI
    root = tk.Tk()
    root.title("Book Word Counts")
    
    canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH)
    canvas.pack()

    background_label = tk.Label(root, bg='#38C0E5')
    background_label.place(relwidth=1, relheight=1)

    #create  frame for entries
    entry_frame = tk.Frame(root, bg='white', bd=5, relief="raised")
    entry_frame.place(relx=0.5, rely=0.05, relwidth=0.75, relheight=0.25, anchor='n')

    # place a label, entry, and button in the first frame
    label = tk.Label(entry_frame, bg="white", text="Enter book title:", font=("Arial", 12))
    label.place(relx=0.0, rely = 0.25, relheight=.2, anchor='w',)
    title_entry = tk.Entry(entry_frame, font=50, borderwidth=2, relief="solid")
    title_entry.place(relx = 0.135, rely = 0.15, relwidth=0.6, relheight=.2)
    button = tk.Button(entry_frame, borderwidth=5, relief="raised", text="Search Title", font=50, command=title_button_clicked)
    button.place(relx=0.75, rely = 0.15, relheight=.2, relwidth=0.2)
    
    # place another label, entry, and button in the first frame
    label = tk.Label(entry_frame, bg="white", text="Enter book URL:", font=("Arial", 12))
    label.place(relx=0.0, rely = 0.7, relheight=.2, anchor='w',)
    url_entry = tk.Entry(entry_frame, font=50, borderwidth=2, relief="solid")
    url_entry.place(relx = 0.135, rely = 0.6, relwidth=0.6, relheight=.2)
    button = tk.Button(entry_frame, borderwidth=5, relief="raised", text="Search URL", font=50, command=url_button_clicked)
    button.place(relx=0.75, rely = 0.6, relheight=.2, relwidth=0.2)

    # create a  frame for the diplaying the title
    title_frame = tk.Frame(root, bg='white', borderwidth=5, relief="raised")
    title_frame.place(relx=0.5, rely=0.33, relwidth=0.75, relheight=0.07, anchor='n')
    
    # create a  frame for displaying word counts
    results_frame = tk.Frame(root, bg='white', borderwidth=5, relief="raised")
    results_frame.place(relx=0.5, rely=0.4, relwidth=0.75, relheight=0.5, anchor='n')



    root.mainloop()
         



