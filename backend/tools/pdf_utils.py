import os
import json
import zipfile
import tempfile
from pathlib import Path
from pypdf import PdfReader, PdfWriter

def save_uploaded_pdfs(uploaded_files, tmp_dir):
  """
  Save each FileStorage in uploaded_files into 
  the temporary directory and return list of paths
  """
  saved_paths = []

  for file_storage in uploaded_files:
    fname = file_storage.filename
    dest = os.path.join(tmp_dir, fname)
    file_storage.save(dest)
    saved_paths.append(dest)

  return saved_paths

def parse_segments_and_names(form):
  """
  Extract and validate the segments and names from
  request.form, raise error if any issues occur
  """
  try:
    segments = json.loads(form.get("segments", "[]"))
    names  = json.loads(form.get("names", "[]"))
  except json.JSONDecodeError:
    raise ValueError("Invalid JSON for segments or names")
  
  # Check if lists and check lengths
  if not isinstance(segments, list) or not isinstance(names, list):
    raise ValueError("'segments' and 'names' must be JSON arrays")
  if len(segments) != len(names):
    raise ValueError("Length of 'segments' must match length of 'names'")
  
  return segments, names

def process_segments(saved_paths, segments, names, tmp_dir):
  """
  For each segment build one separate PDF, returning a list of output
  file paths (raise ValueError on invalid input in 'segments')
  """
  output_paths = []

  # Iterate over each segment
  for i, segment in enumerate(segments):
    if not isinstance(segment, list):
      raise ValueError(f"Segment {i} is not an array")

    writer = PdfWriter()

    # For every range in this segment
    for entry in segment:
      # Each entry should be a dict with fileIndex, startPage, endPage
      if not all(k in entry for k in ("fileIndex", "startPage", "endPage")):
        raise ValueError(f"Invalid 'range' entry in segment {i}")

      file_index = entry["fileIndex"]
      start_page = entry["startPage"]
      end_page   = entry["endPage"]

      # Validate indices
      if (
        not isinstance(file_index, int)
        or file_index < 0
        or file_index >= len(saved_paths)
      ):
        raise ValueError(f"fileIndex out of bounds in segment {i}")
      if (
        not isinstance(start_page, int)
        or not isinstance(end_page, int)
        or start_page < 1
        or end_page < start_page
      ):
        raise ValueError(f"Invalid page range in segment {i}")

      reader = PdfReader(saved_paths[file_index])
      total_pages = len(reader.pages)

      # Make end_pages fit the pdf length if it goes over
      end_page = min(end_page, total_pages)

      # Extract pages
      for pg_num in range(start_page - 1, end_page):
        writer.add_page(reader.pages[pg_num])

    # Write segment’s merged PDF to disk
    out_name = names[i]
    # Ensure it ends with .pdf
    if not out_name.lower().endswith(".pdf"):
      out_name += ".pdf"
    out_path = os.path.join(tmp_dir, out_name)

    with open(out_path, "wb") as out_file:
      writer.write(out_file)

    output_paths.append(out_path)

  return output_paths

def make_zip(output_paths, tmp_dir):
  """
  If we have multiple outputs, package them into a zip and return path
  """

  if len(output_paths) <= 1:
    # send this file only - shouldn't happen with current app.py behaviour
    # but doesn't hurt to have
    return output_paths[0]
  
  zip_path = os.path.join(tmp_dir, "segments_output.zip")
  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for p in output_paths:
      zipf.write(p, arcname=Path(p).name)

  return zip_path