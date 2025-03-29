import React from 'react'
import { Link } from 'react-router-dom';

function NavBar() {
    return (
        <header className='w-full'>
            <nav className='bg-[#DCF2F1] text-black px-5 py-1 md:py-0'>
                <div className="mx-auto flex justify-between items-center w-full">
                    <div className='flex '>
                        <Link to="/">
                            <img src="/img/logo.png" alt="Logo" className='w-[50%]' />
                        </Link>
                    </div>
                    <ul className='flex space-x-2 gap-2 text-sm w-full items-center'>
                        <Link>
                            <li className='text-center h-full px-3 py-5 font-semibold hover:text-white hover:bg-[#003F88] transition-all duration-300 ease-in-out'>Perfil</li>
                        </Link>
                        <Link>
                            <li className='text-center h-full px-3 py-5 font-semibold hover:text-white hover:bg-[#003F88] transition-all duration-300 ease-in-out'>Control IoT</li>
                        </Link>
                        <Link>
                            <li className='text-center h-full px-3 py-5 font-semibold hover:text-white hover:bg-[#003F88] transition-all duration-300 ease-in-out'>Gestión de Registros</li>
                        </Link>
                        <Link>
                            <li className='text-center h-full px-3 py-5 font-semibold hover:text-white hover:bg-[#003F88] transition-all duration-300 ease-in-out'>Facturación</li>
                        </Link>
                        <Link>
                            <li className='text-center h-full px-3 py-5 font-semibold hover:text-white hover:bg-[#003F88] transition-all duration-300 ease-in-out'>Historial de consumo</li>
                        </Link>
                        <Link>
                            <li className='text-center h-full px-3 py-5 font-semibold hover:text-white hover:bg-[#003F88] transition-all duration-300 ease-in-out'>Predicciones</li>
                        </Link>
                        <Link>
                            <li className='text-center h-full px-3 py-5 font-semibold hover:text-white hover:bg-[#003F88] transition-all duration-300 ease-in-out'>Permisos</li>
                        </Link>
                    </ul>
                </div>
            </nav>
        </header>
    )
}

export default NavBar;
