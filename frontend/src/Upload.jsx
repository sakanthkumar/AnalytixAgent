import axios from "axios";
import { useState } from "react";

function Upload({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);

  const upload = async (e, machineName) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    if (machineName) {
      form.append("machine_name", machineName);
    }
    try {
      const res = await axios.post("http://localhost:8000/upload", form);
      if (onUploadSuccess) onUploadSuccess(res.data);
    } catch (e) {
      console.error(e);
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-box">
      <div style={{ marginBottom: "10px" }}>
        <input
          type="text"
          placeholder="Machine Name (e.g. KUKA Robot)"
          id="machine-name"
          style={{ padding: "8px", borderRadius: "4px", border: "1px solid #444", background: "#333", color: "#fff" }}
        />
      </div>
      <label className="upload-btn">
        {uploading ? "Uploading..." : "Click to Upload CSV"}
        <input
          type="file"
          accept=".csv"
          onChange={(e) => {
            const machineName = document.getElementById("machine-name").value;
            upload(e, machineName);
          }}
          style={{ display: 'none' }}
          disabled={uploading}
        />
      </label>
    </div>
  );
}
export default Upload;
