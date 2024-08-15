// DocumentSelector.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://192.168.0.17:5000';

function DocumentSelector() {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState('');
  const [processingStatus, setProcessingStatus] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = () => {
    axios.get(`${API_BASE_URL}/api/documents`)
      .then(response => setDocuments(response.data.documents))
      .catch(error => console.error('Error:', error));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedDoc) {
      navigate(`/view/${selectedDoc}`);
    }
  };

  const handlePreprocess = () => {
    setProcessingStatus('Processing...');
    axios.post(`${API_BASE_URL}/api/process_pdfs`)
      .then(response => {
        setProcessingStatus('Processing completed successfully');
        fetchDocuments(); // Refresh the document list
      })
      .catch(error => {
        console.error('Error:', error);
        setProcessingStatus('Error occurred during processing');
      });
  };

  return (
    <div>
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <div>
          <Button variant="secondary" onClick={handlePreprocess}>
            Preprocess PDFs
          </Button>
          </div>
          <br></br>
          <Form.Label>Select a document</Form.Label>
          <Form.Select
            value={selectedDoc}
            onChange={(e) => setSelectedDoc(e.target.value)}
          >
            <option value="">Choose...</option>
            {documents.map(doc => (
              <option key={doc} value={doc}>{doc}</option>
            ))}
          </Form.Select>
        </Form.Group>
        <Button variant="primary" type="submit" disabled={!selectedDoc} className="me-2">
          View Document
        </Button>

      </Form>
      {processingStatus && (
        <Alert variant={processingStatus.includes('Error') ? 'danger' : 'success'} className="mt-3">
          {processingStatus}
        </Alert>
      )}
    </div>
  );
}

export default DocumentSelector;