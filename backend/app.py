from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile
import os
import zipfile
from pathlib import Path
import json
from pypdf import PdfReader, PdfWriter

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

  # 2) Save all uploaded files to tmp_dir
  uploaded_files = request.files.getlist("files[]")
  if not uploaded_files:
    return jsonify({"error": "No files uploaded"}), 400

  saved_paths = []
  for file_storage in uploaded_files:
    fname = file_storage.filename
    dest = os.path.join(tmp_dir, fname)
    file_storage.save(dest)
    saved_paths.append(dest)

  # raw_segments = request.form.get("segments", "")
  # raw_names  = request.form.get("names", "")
  # print("DEBUG: raw segments string =", repr(raw_segments))
  # print("DEBUG: raw names string  =", repr(raw_names))

  # 3) Parse segments and names from form data
  try:
    segments = json.loads(request.form.get("segments", "[]"))
    names  = json.loads(request.form.get("names", "[]"))
  except json.JSONDecodeError:
    return jsonify({"error": "Invalid JSON for segments or names"}), 400

  # > Check lengths
  if not isinstance(segments, list) or not isinstance(names, list):
    return jsonify({"error": "'segments' and 'names' must be JSON arrays"}), 400
  if len(segments) != len(names):
    return jsonify({"error": "Length of 'segments' must match length of 'names'"}), 400

  output_paths = []

  # 4) Iterate over each segment
  for i, segment in enumerate(segments):
    if not isinstance(segment, list):
      return jsonify({"error": f"Segment {i} is not an array"}), 400

    writer = PdfWriter()

    # 4a) For every range in this segment
    for entry in segment:
      # Each entry should be a dict with fileIndex, startPage, endPage
      if not all(k in entry for k in ("fileIndex", "startPage", "endPage")):
        return jsonify({"error": f"Invalid range entry in segment {i}"}), 400

      file_index = entry["fileIndex"]
      start_page = entry["startPage"]
      end_page   = entry["endPage"]

      # Validate indices
      if (
        not isinstance(file_index, int)
        or file_index < 0
        or file_index >= len(saved_paths)
      ):
        return jsonify({"error": f"fileIndex out of bounds in segment {i}"}), 400
      if (
        not isinstance(start_page, int)
        or not isinstance(end_page, int)
        or start_page < 1
        or end_page < start_page
      ):
        return jsonify({"error": f"Invalid page range in segment {i}"}), 400

      source_path = saved_paths[file_index]
      reader = PdfReader(source_path)
      total_pages = len(reader.pages)

      # Make end_pages fit the pdf length if necessary
      end_page = min(end_page, total_pages)

      # Extract pages
      for pg_num in range(start_page - 1, end_page):
        writer.add_page(reader.pages[pg_num])

    # 4b) Write segment’s merged PDF to disk
    out_name = names[i]
    # Ensure it ends with .pdf
    if not out_name.lower().endswith(".pdf"):
      out_name += ".pdf"
    out_path = os.path.join(tmp_dir, out_name)

    with open(out_path, "wb") as out_file:
      writer.write(out_file)

    output_paths.append(out_path)

  # 5) Return results
  if len(output_paths) == 1:
    # Single output → return that PDF directly
    return send_file(
      output_paths[0],
      as_attachment=True,
      download_name=Path(output_paths[0]).name,
    )

  # Multiple outputs → package into ZIP
  zip_path = os.path.join(tmp_dir, "segments_outputs.zip")
  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for path in output_paths:
      zf.write(path, arcname=Path(path).name)

  return send_file(
    zip_path,
    as_attachment=True,
    download_name="segments_outputs.zip",
  )


if __name__ == "__main__":
  app.run(debug=True)
