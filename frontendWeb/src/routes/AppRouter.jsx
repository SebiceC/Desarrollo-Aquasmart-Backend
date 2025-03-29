import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Login from '../app/auth/Login'
import Home from '../Home'

const AppRouter = () => {
  return (
    <Routes>
        <Route path='/login' element={<Login />} />
        <Route path='/' element={<Home />} />
    </Routes>


  )
}

export default AppRouter;
