// DocumentViewer.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import { Button, Image, Row, Col } from 'react-bootstrap';

const API_BASE_URL = 'http://192.168.0.17:5000';

function DocumentViewer() {
  const { docName } = useParams();
  const [pages, setPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [scale, setScale] = useState(1.0);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/document/${docName}/pages`)
      .then(response => setPages(response.data.pages))
      .catch(error => console.error('Error:', error));
  }, [docName]);

  const handlePrevious = () => setCurrentPage(prev => Math.max(0, prev - 1));
  const handleNext = () => setCurrentPage(prev => Math.min(pages.length - 1, prev + 1));
  const handleZoomIn = () => setScale(prev => prev + 0.1);
  const handleZoomOut = () => setScale(prev => Math.max(0.1, prev - 0.1));

  return (
    <div>
      <h2>{docName}</h2>
      <Row>
        <Col md={3}>
          <div style={{ height: '400px', overflow: 'auto', border: '1px solid #ddd' }}>
            {pages.map((page, index) => (
              <div
                key={index}
                style={{
                  padding: '5px',
                  backgroundColor: currentPage === index ? '#f0f0f0' : 'transparent',
                  cursor: 'pointer'
                }}
                onClick={() => setCurrentPage(index)}
              >
                Page {index + 1}
              </div>
            ))}
          </div>
        </Col>
        <Col md={9}>
          {pages.length > 0 && (
            <div>
            <div className="mt-3">
                <Button onClick={handlePrevious} disabled={currentPage === 0} className="me-2">Previous</Button>
                <Button onClick={handleNext} disabled={currentPage === pages.length - 1} className="me-2">Next</Button>
                <Button onClick={handleZoomOut} className="me-2">Zoom Out</Button>
                <Button onClick={handleZoomIn}>Zoom In</Button>
              </div>
              <p>Page {currentPage + 1} of {pages.length}</p>
              <Image 
                src={`${API_BASE_URL}/api/document/${docName}/page/${pages[currentPage]}`} 
                style={{ width: `${100 * scale}%`, height: 'auto',border: '2px solid black', boxSizing: 'border-box' }}
                alt={`Page ${currentPage + 1}`}
              />
            </div>
          )}
        </Col>
      </Row>
    </div>
  );
}

export default DocumentViewer;