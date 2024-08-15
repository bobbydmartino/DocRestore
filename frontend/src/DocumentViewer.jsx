import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import { Button, Image } from 'react-bootstrap';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';

const API_BASE_URL = 'http://192.168.0.17:5000';

function DocumentViewer() {
  const { docName } = useParams();
  const [pages, setPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [scale, setScale] = useState(1.0);
  const [sliderValue, setSliderValue] = useState(1);
  const imageRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    axios.get(`${API_BASE_URL}/api/document/${docName}/pages`)
      .then(response => setPages(response.data.pages))
      .catch(error => console.error('Error:', error));
  }, [docName]);

  const fitImageToScreen = () => {
    if (imageRef.current && containerRef.current) {
      const img = imageRef.current;
      const container = containerRef.current;
      const availableHeight = window.innerHeight - container.offsetTop - 150; 
      let newScale = 1;

      while (img.offsetHeight * newScale > availableHeight && newScale > 0.1) {
        newScale -= 0.05; 
      }
      setScale(newScale);
    }
  };

  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 20; // Try for 10 seconds (20 * 500ms)
    
    const checkImageAndResize = () => {
      const img = imageRef.current;
      if (img && img.complete && img.naturalHeight !== 0) {
        fitImageToScreen();
      } else if (attempts < maxAttempts) {
        attempts++;
        setTimeout(checkImageAndResize, 10);
      }
    };

    checkImageAndResize();

    return () => {
      attempts = maxAttempts; // Stop the polling if component unmounts
    };
  }, [currentPage]);

  useEffect(() => {
    const handleResize = () => {
      fitImageToScreen();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  const handlePrevious = () => setCurrentPage(prev => Math.max(0, prev - 1));
  const handleNext = () => setCurrentPage(prev => Math.min(pages.length - 1, prev + 1));
  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.1, 3));
  const handleZoomOut = () => setScale(prev => Math.max(0.1, prev - 0.1));

  const handleSliderChange = (value) => {
    setSliderValue(value);
  };

  const handleSliderChangeComplete = (value) => {
    setCurrentPage(value - 1);
  };

  return (
    <div ref={containerRef}>
      <h2>{docName}</h2>
      <div className="mb-3">
        <Slider
          min={1}
          max={pages.length}
          value={sliderValue}
          onChange={handleSliderChange}
          onChangeComplete={handleSliderChangeComplete}
        />
      </div>
      <div className="mb-3">
        <Button onClick={handlePrevious} disabled={currentPage === 0} className="me-2">Previous</Button>
        <Button onClick={handleNext} disabled={currentPage === pages.length - 1} className="me-2">Next</Button>
        <Button onClick={handleZoomOut} className="me-2">Zoom Out</Button>
        <Button onClick={handleZoomIn}>Zoom In</Button>
      </div>
      <p>Page {currentPage + 1} of {pages.length}</p>
      {pages.length > 0 && (
        <div style={{ overflow: 'auto' }}>
          <Image 
            ref={imageRef}
            src={`${API_BASE_URL}/api/document/${docName}/page/${pages[currentPage]}`} 
            style={{ 
              width: 'auto', 
              height: 'auto', 
              maxWidth: '100%',
              transform: `scale(${scale})`,
              transformOrigin: 'top left',
              border: '2px solid black', 
              boxSizing: 'border-box' 
            }}
            alt={`Page ${currentPage + 1}`}
          />
        </div>
      )}
    </div>
  );
}

export default DocumentViewer;