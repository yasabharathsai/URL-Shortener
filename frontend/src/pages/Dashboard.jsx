import "./Dashboard.css";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Dashboard() {
  const navigate = useNavigate();
  const [expiresAt, setExpiresAt] =
  useState("");
  const [url, setUrl] = useState("");
  const [urls, setUrls] = useState([]);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] =
  useState(false);
  const [loading, setLoading] =
  useState(false);

const [analyticsData,
  setAnalyticsData] =
  useState(null);

  const token = localStorage.getItem("token");

  const headers = {
    Authorization: `Bearer ${token}`,
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  const fetchUrls = async () => {
    try {
      const response = await api.get("/all", {
        headers,
      });

      setUrls(response.data);
    } catch (error) {
      console.log(error);
    }
  };

  useEffect(() => {
    if (!token) {
      navigate("/");
      return;
    }

    fetchUrls();
  }, []);

  const deleteUrl = async (
    shortCode
  ) => {
    const confirmDelete =
      window.confirm(
        "Are you sure you want to delete this URL?"
      );
  
    if (!confirmDelete) {
      return;
    }
  
    try {
      await api.delete(
        `/delete/${shortCode}`,
        {
          headers,
        }
      );
  
      fetchUrls();
    } catch (error) {
      console.log(error);
    }
  };

  const analytics = async (shortCode) => {
    try {
      const response = await api.get(
        `/analytics/${shortCode}`,
        {
          headers,
        }
      );
  
      setAnalyticsData(response.data);
      setShowModal(true);
    } catch (error) {
      console.log(error);
    }
  };


  const updateUrl = async (shortCode) => {
    const newUrl = prompt("Enter new URL");

    if (!newUrl) return;

    try {
      await api.put(
        `/update/${shortCode}`,
        {
          original_url: newUrl,
        },
        {
          headers,
        }
      );

      fetchUrls();
    } catch (error) {
      console.log(error);
    }
  };

  const filteredUrls = urls.filter((item) =>
    item.short_code
      .toLowerCase()
      .includes(search.toLowerCase())
  );
  const totalUrls = urls.length;

const totalClicks = urls.reduce(
  (sum, item) =>
    sum + item.clicks,
  0
);

const activeUrls = urls.filter(
  (item) =>
    !item.expires_at ||
    new Date(item.expires_at) >
      new Date()
).length;

const handleSubmit = async (e) => {
  e.preventDefault();

  try {
    setLoading(true);

    await api.post(
      "/shorten",
      {
        original_url: url,
        expires_at:
          expiresAt || null,
      },
      {
        headers,
      }
    );

    setUrl("");
    setExpiresAt("");
    fetchUrls();

    setLoading(false);
  } catch (error) {
    console.log(error);
    setLoading(false);
  }
};

  return (
    <div className="container">
      {showModal && analyticsData && (
  <div className="modal-overlay">
    <div className="modal-box">
      <h2>Analytics</h2>

      <p>
        <strong>Original URL:</strong>
        <br />
        {analyticsData.original_url}
      </p>

      <p>
        <strong>Clicks:</strong>{" "}
        {analyticsData.clicks}
      </p>

      <p>
        <strong>Created At:</strong>
        <br />
        {analyticsData.created_at}
      </p>

      <p>
        <strong>Expires At:</strong>
        <br />
        {analyticsData.expires_at || "Never"}
      </p>

      <button
        onClick={() =>
          setShowModal(false)
        }
      >
        Close
      </button>
    </div>
  </div>
)}
      <h1>URL Shortener Dashboard</h1>

      <button onClick={logout}>Logout</button>

      <form onSubmit={handleSubmit} className="form">
        <input
          type="text"
          placeholder="Enter URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

<label>
  Expiry Date (Optional)
</label>
<br />
        <input
  type="datetime-local"
  value={expiresAt}
  onChange={(e) =>
    setExpiresAt(e.target.value)
  }
/>

<button
  type="submit"
  disabled={loading}
>
  {
    loading
      ? "Creating..."
      : "Shorten"
  }
</button>
      </form>

      <hr />
      <div className="stats">

  <div className="stat-card">
    <h3>{totalUrls}</h3>
    <p>Total URLs</p>
  </div>

  <div className="stat-card">
    <h3>{totalClicks}</h3>
    <p>Total Clicks</p>
  </div>

  <div className="stat-card">
    <h3>{activeUrls}</h3>
    <p>Active URLs</p>
  </div>

</div>

      <h2>My URLs</h2>

      <input
        type="text"
        placeholder="Search by Short Code"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {urls.length === 0 ? (
        <p>No URLs Found</p>
      ) : filteredUrls.length === 0 ? (
        <p>No URLs Found</p>
      ) : (
        filteredUrls.map((item) => (
          <div
            key={item.short_code}
            className="card"
          >
            <h3>Short URL</h3>

            <p>{item.original_url}</p>

            <p>Clicks: {item.clicks}</p>
            <p>
  Expires:
  {" "}
  {
    item.expires_at
      ? new Date(
          item.expires_at
        ).toLocaleString()
      : "Never"
  }
</p>
{
  item.expires_at &&
  new Date(item.expires_at)
    < new Date() ? (
      <p style={{ color: "red" }}>
        Expired
      </p>
    ) : (
      <p style={{ color: "green" }}>
        Active
      </p>
    )
}

            <a
              href={item.short_url}
              target="_blank"
              rel="noreferrer"
            >
              {item.short_url}
            </a>

            <div className="actions">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(
                    item.short_url
                  );
                  alert(
                    "Short URL copied to clipboard!"
                  );
                }}
              >
                Copy
              </button>

              <button
                onClick={() =>
                  analytics(item.short_code)
                }
              >
                Analytics
              </button>

              <button
                onClick={() =>
                  updateUrl(item.short_code)
                }
              >
                Update
              </button>

              <a
  href={`https://url-shortener-api-bk8f.onrender.com/qr/${item.short_code}`}
  target="_blank"
  rel="noreferrer"
>
  QR Code
</a>

              <button
                onClick={() =>
                  deleteUrl(item.short_code)
                }
              >
                Delete
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default Dashboard;