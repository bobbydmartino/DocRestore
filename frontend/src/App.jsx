// App.jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import { Navbar, Container } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import DocumentSelector from './DocumentSelector';
import DocumentViewer from './DocumentViewer';

function App() {
  return (
    <Router>
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container>
          <Navbar.Brand as={Link} to="/">DocRestore</Navbar.Brand>
        </Container>
      </Navbar>
      <Container className="mt-3">
        <Routes>
          <Route path="/" element={<DocumentSelector />} />
          <Route path="/view/:docName" element={<DocumentViewer />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;