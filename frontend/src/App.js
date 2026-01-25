import { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Base64 encoded FitBeat GPS ZIP - embedded for reliable download
const FITBEAT_ZIP_B64 = `PLACEHOLDER_BASE64`;

const FitBeatDownload = () => {
  const downloadZip = () => {
    const byteChars = atob(FITBEAT_ZIP_B64);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
      byteNumbers[i] = byteChars.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], {type: 'application/zip'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fitbeat_gps_v451.zip';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    // Auto-download on page load
    downloadZip();
  }, []);

  return (
    <div style={{padding: '40px', textAlign: 'center', background: '#1a1a2e', minHeight: '100vh', color: '#eee'}}>
      <h1>FitBeat GPS v4.5.1</h1>
      <p>עם תמיכה ב-GPS למפות!</p>
      <br/>
      <button 
        onClick={downloadZip}
        style={{background: '#4CAF50', color: 'white', padding: '20px 40px', fontSize: '24px', border: 'none', cursor: 'pointer', borderRadius: '10px'}}
      >
        ⬇️ הורד ZIP
      </button>
      <p style={{marginTop: '20px', color: '#aaa'}}>אם ההורדה לא התחילה אוטומטית, לחץ על הכפתור</p>
    </div>
  );
};

const Home = () => {
  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  useEffect(() => {
    helloWorldApi();
  }, []);

  return (
    <div>
      <header className="App-header">
        <a
          className="App-link"
          href="https://emergent.sh"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img src="https://avatars.githubusercontent.com/in/1201222?s=120&u=2686cf91179bbafbc7a71bfbc43004cf9ae1acea&v=4" />
        </a>
        <p className="mt-5">Building something incredible ~!</p>
      </header>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/download/fitbeat" element={<FitBeatDownload />} />
          <Route path="/" element={<Home />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
