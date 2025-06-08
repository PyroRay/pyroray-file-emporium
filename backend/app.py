from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile
from pathlib import Path
import os
# import zipfile
# import json
# from pypdf import PdfReader, PdfWriter

from tools.pdf_utils import (
    save_uploaded_pdfs,
    parse_segments_and_names,
    process_segments,
)

from tools.file_utils import (
  chunk_file,
  reassemble_file,
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
      download_name="pdf_segments.zip",
  )

@app.route("/api/file/chunk", methods=["POST"])
def file_chunk():
  # 1) Make a temp directory and save the single upload
  tmp_dir = tempfile.mkdtemp()
  upload = request.files.get("file")
  if not upload: return jsonify({"error": "No file uploaded"}), 400
  input_path = os.path.join(tmp_dir, upload.filename)
  upload.save(input_path)

  # 2) Get chunk size in bytes form
  try:
    chunk_size = int(request.form.get("chunkSize", "0"))
    assert chunk_size > 0
  except:
    return jsonify({"error": "Invalid or missing chunkSize"}), 400
  
  # 3) Split the file
  chunks = chunk_file(input_path, chunk_size)

  # 4) Compress the files into a zip
  zip_path = make_zip(chunks, tmp_dir)
  return send_file(
      zip_path,
      as_attachment=True,
      download_name="chunks.zip",
  )
  

@app.route("/api/file/reassemble", methods=["POST"])
def file_reassemble():
  # 1) tmp dir & save all chunk uploads
  tmp_dir = tempfile.mkdtemp()
  uploads = request.files.getlist("files[]")
  if not uploads:
    return jsonify({"error": "No chunk files uploaded"}), 400

  paths = []
  for f in uploads:
    destination = os.path.join(tmp_dir, f.filename)
    f.save(destination)
    paths.append(destination)

  # 2) sort them by filename so they’re in correct order
  # because of this it probably wont work well if you upload
  # files that aren't ordered by name
  paths.sort()

  # 3) reassemble
  out_name = request.form.get("outputName", "reassembled")
  if not out_name.lower().endswith(".bin"):
    out_name += ".bin"
  out_path = os.path.join(tmp_dir, out_name)
  reassemble_file(paths, out_path)

  return send_file(
    out_path,
    as_attachment=True,
    download_name=out_name,
  )

if __name__ == "__main__":
  app.run(debug=True)
