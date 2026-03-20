💬 LAN Chat - Private Local Messenger

A modern, real-time private messaging and file-sharing web application designed for local networks (LAN/WiFi). No database, no login credentials, no cloud storage. Just fast, private, and temporary communication.

PythonFlaskLicense
✨ Features

    📡 Local Network Ready: Works on any WiFi network using the host's local IP.
    🔒 Private Messaging: Real-time one-to-one chat using Socket.IO.
    📂 File Sharing: Share images, PDFs, and documents (up to 50MB) securely.
    💾 Zero Storage: Messages exist only in memory. No database, no history, full privacy.
    🎨 Modern UI: Dark-themed, responsive interface inspired by modern messaging apps.
    ⌨️ Typing Indicators: See when the other person is typing.
    🟢 Online Status: View active users in the sidebar.

📸 Screenshots

(Tip: Take a screenshot of your app running, save it in a folder named screenshots, and link it here)
🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.
Prerequisites

    Python 3.8 or higher
    A device connected to a local WiFi network


Installation


---Clone the repository---

git clone https://github.com/your-username/lan-chat-app.gitcd lan-chat-app

Create a virtual environment (Optional but recommended) 
    
----bash---- 

    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
      

Install dependencies 

----bash---- 
    pip install -r requirements.txt
     
     
      

Run the application 

----bash----  
    python app.py
     
     
      

    Access the App 
         The terminal will display the local IP address.
         Open http://<local-ip>:5000 in your browser.
         Share this address with others on the same WiFi network.
          

🛠️ Tech Stack 

     Backend: Python, Flask, Flask-SocketIO
     Frontend: HTML5, CSS3, JavaScript (Vanilla), Tailwind CSS (CDN)
     Real-time Engine: Socket.IO
     

📝 License 

This project is licensed under the MIT License - see the LICENSE  file for details. 
🤝 Contributing 

Contributions, issues, and feature requests are welcome! Feel free to check the issues page. 

Made with ❤️ by [Varun Rajput] 