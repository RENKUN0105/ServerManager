from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
  return "ServerBot起動中"

def run():
  app.run(host="0.0.0.0", port=8080)

def open():
  server = Thread(target=run)
  server.start()