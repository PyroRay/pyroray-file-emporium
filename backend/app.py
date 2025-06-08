from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile
from pathlib import Path
# import os
# import zipfile
# import json
# from pypdf import PdfReader, PdfWriter

from tools.pdf_utils import (
    save_uploaded_pdfs,
    parse_segments_and_names,
    process_segments,
    make_zip,
)

app = Flask(__name__)
CORS(app)


@app.route("/api/pdf/segments", methods=["POST"])
def pdf_segments():
  """
  Expects multipart/form-data:
    files[]: array of uploaded PDF files
    segments: JSON‐encoded array of segments, where each segment is an
        array of dictionaries with the keys being:
        { fileIndex, startPage, endPage }
    names: JSON‐encoded array of output filenames, one per segment

  Behavior:
    For each segment i:
    1. Create a new PDF writer.
    2. For each range entry in segments[i]:
      > Load source PDF from files[fileIndex].
      > Extract pages from startPage through endPage (inclusive)
      > Add those pages in order to the writer.
    3. Write the writer content to disk as names[i].
    
    After segments are written:
    > If there is exactly one output file, return it directly.
    > Otherwise, ZIP all output files and return the ZIP.
  """

  # 1) Create temporary workspace
  tmp_dir = tempfile.mkdtemp()

  # 2) Save uploaded files to tmp_dir
  uploaded_files = request.files.getlist("files[]")
  if not uploaded_files:
    return jsonify({"error": "No files uploaded"}), 400
  
  saved_paths = save_uploaded_pdfs(uploaded_files, tmp_dir)

  # 3) Parse and validate JSONs
  try:
    segments, names = parse_segments_and_names(request.form)
  except ValueError as e:
    return jsonify({"error": str(e)}), 400
  
  # 4) Prcocess segments into into pdfs
  try:
    output_paths = process_segments(saved_paths, segments, names, tmp_dir)
  except ValueError as e:
    return jsonify({"error": str(e)}), 400
  
  # 5) Return PDF or ZIP depending on how many there are
  if len(output_paths) == 1:
    return send_file(
      output_paths[0], 
      as_attachment=True,
      download_name=Path(output_paths[0]).name,
    )
  
  zip_path = make_zip(output_paths, tmp_dir)
  return send_file(
      zip_path,
      as_attachment=True,
      download_name=Path(zip_path).name,
  )

if __name__ == "__main__":
  app.run(debug=True)
