import os
import tempfile
import zipfile
from pathlib import Path

def chunk_file(input_path: str, chunk_size: int) -> list[str]:
  """
  Split file at 'input_path' into sequential chunks of up to 'chunk_size' 
  bytes, returning a list of chunk file paths in a new temporary directory
  """
  name = os.path.splitext(os.path.basename(input_path))[0]
  tmp_dir = tempfile.mkdtemp()
  chunk_paths = []

  with open(input_path, 'rb') as source:
    index = 0
    while True:
      data = source.read(chunk_size)
      if not data: break
      chunk_name = f"{name}_part_{index:04d}"
      chunk_path = os.path.join(tmp_dir, chunk_name)
      with open(chunk_path, "wb") as out:
        out.write(data)
      chunk_paths.append(chunk_path)
      index += 1

  return chunk_paths

def reassemble_file(chunk_paths: list[str], output_path: str) -> None:
  """
  Concatenates the files in 'chunk_paths' into 'output_path' in order
  """
  with open(output_path, "wb") as destination:
    for p in chunk_paths:
      with open(p, "rb") as source:
        destination.write(source.read())

def make_zip(output_paths, tmp_dir):
  """
  If we have multiple outputs, package them into a zip and return path
  Otherwise return just the filepath of the only file
  """

  if len(output_paths) <= 1:
    return output_paths[0]
  
  zip_path = os.path.join(tmp_dir, "output.zip")
  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for p in output_paths:
      zipf.write(p, arcname=Path(p).name)

  return zip_path
