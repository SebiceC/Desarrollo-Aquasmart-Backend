import React, { useState, useEffect } from 'react';
import axios from 'axios';
import InputItem from '../../components/InputItem';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const [document, setDocument] = useState('');
    const [password, setPassword] = useState('');
    const [otp, setOtp] = useState('');
    const [error, setError] = useState('');
    const [otpError, setOtpError] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [showTokenForm, setShowTokenForm] = useState(false);
    const [timeLeft, setTimeLeft] = useState(0);
    const [isDisabled, setIsDisabled] = useState(false);
    const navigate = useNavigate();

    // Función para manejar el login
    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            const response = await axios.post('https://4q190rbc-8000.use.devtunnels.ms/api/users/login', {
                document,
                password
            });

            setShowModal(true);
        } catch (err) {
            setError('¡Campos vacíos o credenciales incorrectas!');
            console.error(err);
        }
    };

    // Manejar la confirmación del modal para mostrar el formulario de token
    const handleConfirm = () => {
        setShowModal(false);
        setShowTokenForm(true);
        startTimer();
    };

    // Iniciar el temporizador de 15 minutos
    const startTimer = () => {
        setTimeLeft(900);
        setIsDisabled(true);
    };

    // Manejar la cuenta regresiva
    useEffect(() => {
        if (timeLeft > 0) {
            const timer = setInterval(() => {
                setTimeLeft((prev) => prev - 1);
            }, 1000);

            return () => clearInterval(timer);
        } else {
            setIsDisabled(false);
        }
    }, [timeLeft]);

    // Formatear tiempo en MM:SS
    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${secs < 10 ? "0" : ""}${secs}`;
    };

    // Manejar el envío del token
    const handleTokenSubmit = async () => {
        try {
            const response = await axios.post('https://4q190rbc-8000.use.devtunnels.ms/api/users/validate-otp', {
                document,
                otp
            });

            if (response.data.access) {
                localStorage.setItem('token', response.data.access);
                localStorage.setItem('refresh', response.data.refresh);
                navigate('/');
            } else {
                setOtpError('El token ingresado es incorrecto.');
            }
        } catch (err) {
            setOtpError('Error al validar el token, intenta nuevamente.');
            console.error(err);
        }
    };

    return (
        <div className="w-full h-full min-h-screen bg-[#DCF2F1] flex flex-col items-center justify-center gap-10">
            <div className='flex justify-center'>
                <img src="/img/logo.png" alt="Logo" className='w-full lg:w-[50%]' />
            </div>

            {!showTokenForm ? (
                <div className="w-[70%] lg:w-[30%] bg-white p-6 border-1 border-[#003F88] rounded-lg mx-auto flex flex-col justify-center items-center">
                    <h1 className='text-4xl font-bold pb-8 text-center'>INICIO DE SESIÓN</h1>
                    <form onSubmit={handleLogin} className='flex flex-col items-center w-full'>
                        {error && (
                            <span className='w-[80%] text-md text-center py-1 mb-2 bg-[#FFA7A9] rounded-lg text-gray-600'>
                                {error}
                            </span>
                        )}
                        <InputItem
                            id="document"
                            labelName="Cédula de Ciudadanía"
                            placeholder="Ingresa tu Cédula de Ciudadanía"
                            type="string"
                            value={document}
                            onChange={(e) => setDocument(e.target.value)}
                        />
                        <InputItem
                            id="password"
                            labelName="Contraseña"
                            placeholder="Ingresa tu contraseña"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        <div className="flex flex-col items-center gap-2">
                            <a href="#" className='font-semibold text-sm hover:underline'>OLVIDÉ MI CONTRASEÑA</a>
                            <a href="#" className='font-semibold text-sm hover:underline'>SOY USUARIO NUEVO</a>
                        </div>
                        <button type="submit" className="w-[60%] sm:w-[35%] mt-4 bg-[#365486] text-white py-2 px-2 rounded-lg hover:bg-[#344663] hover:scale-105 transition-all duration-300 ease-in-out">
                            INICIAR SESIÓN
                        </button>
                    </form>
                </div>
            ) : (
                <div className="bg-white p-8 rounded-lg shadow-lg w-[400px] border border-blue-400">
                    <h2 className="text-2xl font-bold text-center">INGRESO DE TOKEN</h2>
                    <p className="text-center mt-2">Introduce el token que fue enviado por SMS a tu teléfono.</p>

                    <div className="flex justify-center gap-2 mt-4">
                        {otpError && (
                            <span className='w-[80%] text-md text-center py-1 mb-2 bg-[#FFA7A9] rounded-lg text-gray-600'>
                                {otpError}
                            </span>
                        )}
                        {[...Array(6)].map((_, i) => (
                            <input
                                key={i}
                                type="string"
                                maxLength="1"
                                className="w-12 h-12 text-center border border-gray-400 rounded-md"
                                value={otp[i] || ''}
                                onChange={(e) => {
                                    let newOtp = otp.split('');
                                    newOtp[i] = e.target.value;
                                    setOtp(newOtp.join(''));
                                }}
                            />
                        ))}
                    </div>

                    <p className="text-center text-gray-600 mt-2">
                        {timeLeft > 0 ? `Tiempo restante: ${formatTime(timeLeft)}` : "Puedes solicitar un nuevo token"}
                    </p>

                    <div className="flex justify-center gap-4 mt-4">
                        <button
                            onClick={startTimer}
                            disabled={isDisabled}
                            className={`px-4 py-2 rounded-lg text-white font-semibold transition-all duration-300 ${isDisabled ? "bg-gray-400 cursor-not-allowed" : "bg-[#365486] hover:bg-[#344663]"
                                }`}
                        >
                            SOLICITAR NUEVO TOKEN
                        </button>
                        <button onClick={handleTokenSubmit} className="bg-[#365486] text-white px-4 py-2 rounded-lg hover:bg-[#344663]">
                            ENVIAR
                        </button>
                    </div>
                </div>
            )}

            {showModal && (
                <div className="fixed inset-0 flex items-center justify-center bg-opacity-50 backdrop-blur-sm">
                    <div className="bg-white p-6 rounded-lg shadow-lg text-center w-[90%] sm:w-[400px]">
                        <h2 className="text-xl font-bold mb-4">TOKEN ENVIADO</h2>
                        <p>Se ha enviado un token de 6 caracteres a tu número de teléfono registrado.</p>
                        <button onClick={handleConfirm} className="bg-[#365486] text-white px-4 py-2 rounded-lg hover:bg-[#344663]">
                            CONFIRMAR
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Login;
