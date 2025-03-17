import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import "./styles/App.scss";
import { GiHamburgerMenu } from "react-icons/gi";

function App() {
  const [count, setCount] = useState(0);

  return (
    <>
      <header
        style={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "space-between",
          padding: "8px",
          margin: "10px",
        }}
      >
        <img
          src="./Levrum-logo-square.png"
          alt="Levrum"
          style={{ width: "20px", height: "25px" }}
        />
        <GiHamburgerMenu style={{ width: "20px", height: "25px" }} />
      </header>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </Router>
    </>
  );
}

export default App;
