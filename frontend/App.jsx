import "./App.css";

function App() {
  return (
    <div className="app">
      <h1>Financial Research Assistant</h1>

      <div className="cards">
        <div className="card">
          <h2>Create Research Session</h2>
          <p>Start AI-powered financial analysis.</p>
          <button>Create</button>
        </div>

        <div className="card">
          <h2>Upload Documents</h2>
          <p>Upload company reports and PDFs.</p>
          <button>Upload PDF</button>
        </div>

        <div className="card">
          <h2>Research Workspace</h2>
          <p>Ask questions and get cited answers.</p>
          <button>Open Chat</button>
        </div>

        <div className="card">
          <h2>Company Comparison</h2>
          <p>Compare financial metrics.</p>
          <button>Compare</button>
        </div>
      </div>
    </div>
  );
}

export default App;
