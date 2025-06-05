import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <div>
      <h1>PyroRay’s File Emporium</h1>
      <p>Select a tool below to get started:</p>
      <ul>
        <li>
          <Link to="/pdf-tool">PDF Splitter/Merger</Link>
          <p>Split or merge one or more PDFs</p>
        </li>
        <li>
          <Link to="/file-tool">File Splitter/Reassembler</Link>
          <p>Split files into smaller files for later reassembly</p>
        </li>
      </ul>
    </div>
  );
}
