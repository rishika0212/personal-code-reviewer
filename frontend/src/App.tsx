import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Review from './pages/Review'

function App() {
  return (
    <div className="min-h-screen">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/review/:reviewId" element={<Review />} />
      </Routes>
    </div>
  )
}

export default App
