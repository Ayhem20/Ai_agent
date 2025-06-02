import React from 'react';
import './App.css';
import ChatComponent from './components/ChatComponent';

function App() {
  return (
    <div className="App">
      <div className="background-animation">
        <div className="gradient-sphere sphere-1"></div>
        <div className="gradient-sphere sphere-2"></div>
        <div className="gradient-sphere sphere-3"></div>
        <div className="noise-overlay"></div>
      </div>
      
      <header className="App-header">
        <div className="header-content">
          <img 
            src="/triskell-symbol-200px.png" 
            alt="Triskell Logo" 
            className="App-logo" 
          />
          <h1>Triskell AI Assistant</h1>
        </div>
      </header>
      
      <main>
        <ChatComponent />
      </main>
      
      <footer>
        <p>Powered by Triskell - © 2025</p>
      </footer>
    </div>
  );
}

export default App;
