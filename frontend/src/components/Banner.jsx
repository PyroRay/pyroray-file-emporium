import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import "./Banner.css";

// import icons
import homeIcon from "../assets/icons/home.svg";
import pdfIcon from "../assets/icons/pdf-file.svg";
import fileIcon from "../assets/icons/generic-file.svg";

export default function Banner() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`banner ${collapsed ? "collapsed" : ""}`}>
      {/* Collapse/Expand button */}
      <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
        {collapsed ? "≡" : "«"}
      </button>

      {/* Title (hidden when collapsed) */}
      {!collapsed && <h2 className="banner-title">PyroRay’s File Emporium</h2>}

      <nav className="banner-nav">
        <ul>
          <li>
            <NavLink to="/" className="banner-link" end>
              <img src={homeIcon} alt="Home" className="link-icon" />
              {!collapsed && <span className="link-text">Home</span>}
            </NavLink>
          </li>
          <li>
            <NavLink to="/pdf-tool" className="banner-link">
              <img src={pdfIcon} alt="PDF" className="link-icon" />
              {!collapsed && <span className="link-text">PDF Tool</span>}
            </NavLink>
          </li>
          <li>
            <NavLink to="/file-tool" className="banner-link">
              <img src={fileIcon} alt="File" className="link-icon" />
              {!collapsed && <span className="link-text">File Tool</span>}
            </NavLink>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
