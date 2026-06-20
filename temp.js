
        const API_URL = "";
        let miGrafico = null; // Instancia global de Chart.js
        let miCalendario = null; // Instancia global de FullCalendar
        
        // --- AUTENTICACIÓN ---
        let isLoginMode = true;

        function toggleAuthMode() {
            isLoginMode = !isLoginMode;
            document.getElementById("authTitle").textContent = isLoginMode ? "¡Bienvenida de vuelta! ✨" : "Únete a la Magia 🌸";
            document.getElementById("authSubtitle").textContent = isLoginMode ? "Ingresa a tu espacio mágico." : "Crea tu cuenta para empezar.";
            document.getElementById("authSubmitBtn").textContent = isLoginMode ? "Entrar" : "Registrarse";
            document.getElementById("authEmail").style.display = isLoginMode ? "none" : "block";
            document.getElementById("authEmail").required = !isLoginMode;
            document.getElementById("forgotPasswordContainer").style.display = isLoginMode ? "block" : "none";
            document.getElementById("authToggleText").innerHTML = isLoginMode 
                ? '¿No tienes cuenta? <span onclick="toggleAuthMode()">Regístrate aquí</span>'
                : '¿Ya tienes cuenta? <span onclick="toggleAuthMode()">Inicia sesión aquí</span>';
        }

        // --- RECUPERAR CONTRASEÑA ---
        function abrirModalRecuperacion(e) {
            if (e) e.preventDefault();
            document.getElementById("recuperarModal").style.display = "flex";
        }
        
        function cerrarModalRecuperacion(e) {
            if (e) e.preventDefault();
            document.getElementById("recuperarModal").style.display = "none";
            document.getElementById("recuperarEmail").value = "";
        }
        
        async function enviarRecuperacion(e) {
            e.preventDefault();
            const email = document.getElementById("recuperarEmail").value;
            showNotification("Enviando correo mágico... 🕊️", "info");
            try {
                const response = await fetch(`${API_URL}/api/recuperar-password`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await response.json();
                if (response.ok) {
                    showNotification(data.mensaje, "success");
                    cerrarModalRecuperacion();
                } else {
                    showNotification(data.detail || "Error enviando correo.", "error");
                }
            } catch (error) {
                console.error("Error al recuperar:", error);
                showNotification("No pudimos conectar con el servidor.", "error");
            }
        }

        // --- CONFIGURACIÓN DE USUARIO ---
        function abrirConfiguracion() {
            document.getElementById("configModal").style.display = "flex";
            document.getElementById("configUsername").value = localStorage.getItem("lunita_user") || "";
            document.getElementById("configEmail").value = "";
            document.getElementById("configPassword").value = "";
        }

        function cerrarModalConfiguracion(e) {
            if (e) e.preventDefault();
            document.getElementById("configModal").style.display = "none";
        }

        // --- TEMA (DARK/LIGHT MODE) ---
        function inicializarTema() {
            const savedTheme = localStorage.getItem('lunita_theme') || 'system';
            aplicarTema(savedTheme);
            actualizarBotonesTema(savedTheme);

            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                if (localStorage.getItem('lunita_theme') === 'system') {
                    aplicarTema('system');
                }
            });
        }

        function setTema(theme) {
            localStorage.setItem('lunita_theme', theme);
            aplicarTema(theme);
            actualizarBotonesTema(theme);
        }

        function aplicarTema(theme) {
            let esOscuro = false;
            if (theme === 'dark') {
                esOscuro = true;
            } else if (theme === 'system') {
                esOscuro = window.matchMedia('(prefers-color-scheme: dark)').matches;
            }
            
            if (esOscuro) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        }

        function actualizarBotonesTema(theme) {
            document.getElementById('btnThemeLight')?.classList.remove('active-theme-btn');
            document.getElementById('btnThemeDark')?.classList.remove('active-theme-btn');
            document.getElementById('btnThemeSystem')?.classList.remove('active-theme-btn');
            
            if (theme === 'light') document.getElementById('btnThemeLight')?.classList.add('active-theme-btn');
            if (theme === 'dark') document.getElementById('btnThemeDark')?.classList.add('active-theme-btn');
            if (theme === 'system') document.getElementById('btnThemeSystem')?.classList.add('active-theme-btn');
        }

        // --- DATOS DE SALUD ---
        function exportarDatos() {
            const token = localStorage.getItem("lunita_token");
            if (!token) return;
            fetch(`${API_URL}/api/registros`, { headers: getAuthHeaders() })
                .then(res => res.json())
                .then(data => {
                    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
                    const downloadAnchorNode = document.createElement('a');
                    downloadAnchorNode.setAttribute("href", dataStr);
                    downloadAnchorNode.setAttribute("download", "lunita_diario.json");
                    document.body.appendChild(downloadAnchorNode);
                    downloadAnchorNode.click();
                    downloadAnchorNode.remove();
                    showNotification("Datos exportados exitosamente 📥", "success");
                })
                .catch(err => {
                    console.error("Error al exportar:", err);
                    showNotification("Error al exportar datos.", "error");
                });
        }

        async function confirmarBorrarDiario() {
            if (confirm("⚠️ ¿Estás segura de que quieres BORRAR todo tu diario? Esta acción no se puede deshacer.")) {
                if (confirm("💔 Última advertencia: Si estás segura, presiona OK para eliminar todos tus registros de Lunita.")) {
                    const token = localStorage.getItem("lunita_token");
                    if (!token) return;
                    
                    try {
                        const response = await fetch(`${API_URL}/api/registros`, {
                            method: "DELETE",
                            headers: getAuthHeaders()
                        });
                        const data = await response.json();
                        if (response.ok) {
                            showNotification("Tu diario ha sido borrado.", "success");
                            cargarHistorial();
                            cerrarModalConfiguracion();
                        } else {
                            showNotification(data.detail || "Error al borrar el diario.", "error");
                        }
                    } catch (error) {
                        showNotification("Error de conexión.", "error");
                    }
                }
            }
        }

        async function guardarConfiguracion(e) {
            e.preventDefault();
            const newUsername = document.getElementById("configUsername").value.trim();
            const newEmail = document.getElementById("configEmail").value.trim();
            const newPassword = document.getElementById("configPassword").value.trim();
            
            const payload = {};
            if (newUsername && newUsername !== localStorage.getItem("lunita_user")) payload.username = newUsername;
            if (newEmail) payload.email = newEmail;
            if (newPassword) payload.password = newPassword;
            
            if (Object.keys(payload).length === 0) {
                showNotification("No hay cambios para guardar.", "info");
                cerrarModalConfiguracion();
                return;
            }
            
            try {
                const response = await fetch(`${API_URL}/api/usuario/configuracion`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem("lunita_token")}`
                    },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                if (response.ok) {
                    showNotification(data.mensaje, "success");
                    if (payload.username) {
                        localStorage.setItem("lunita_user", payload.username);
                        document.getElementById("userNameDisplay").textContent = payload.username;
                    }
                    cerrarModalConfiguracion();
                } else {
                    showNotification(data.detail || "Error guardando configuración.", "error");
                }
            } catch (error) {
                console.error("Error en configuración:", error);
                showNotification("No se pudo conectar con el servidor.", "error");
            }
        }

        async function handleAuth(e) {
            e.preventDefault();
            const username = document.getElementById("authUsername").value;
            const password = document.getElementById("authPassword").value;
            
            if (isLoginMode) {
                // Login
                try {
                    const params = new URLSearchParams();
                    params.append('username', username);
                    params.append('password', password);
                    
                    const response = await fetch(`${API_URL}/api/token`, {
                        method: 'POST',
                        body: params
                    });
                    
                    if (!response.ok) throw new Error("Usuario o contraseña incorrectos");
                    const data = await response.json();
                    localStorage.setItem("lunita_token", data.access_token);
                    localStorage.setItem("lunita_user", username);
                    showNotification("¡Bienvenida " + username + "! 💖", "success");
                    iniciarApp();
                } catch (error) {
                    console.error("Error en Login:", error);
                    showNotification(error.message, "error");
                }
            } else {
                // Registro
                const email = document.getElementById("authEmail").value;
                try {
                    const response = await fetch(`${API_URL}/api/registro`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, email, password })
                    });
                    
                    if (!response.ok) {
                        const err = await response.json();
                        throw new Error(err.detail);
                    }
                    showNotification("Cuenta creada exitosamente. ¡Inicia sesión! 🌸", "success");
                    toggleAuthMode();
                } catch (error) {
                    console.error("Error en Registro:", error);
                    showNotification(error.message, "error");
                }
            }
        }

        function logout() {
            localStorage.removeItem("lunita_token");
            localStorage.removeItem("lunita_user");
            location.reload();
        }

        function getAuthHeaders() {
            const token = localStorage.getItem("lunita_token");
            return token ? { "Authorization": `Bearer ${token}` } : {};
        }

        function iniciarApp() {
            document.getElementById("authContainer").style.display = "none";
            document.getElementById("dashboardContainer").style.display = "grid";
            document.getElementById("topNav").style.display = "flex";
            document.getElementById("userNameDisplay").textContent = `¡Hola, ${localStorage.getItem("lunita_user")}!`;
            
            const hoy = new Date().toISOString().split('T')[0];
            document.getElementById('fecha').value = hoy;
            
            inicializarCalendario();
            verificarAPI();
            cargarHistorial();
            renderizarGrafico();
            cargarNotificaciones();
            cargarEstadoActual();
        }

        // --- NOTIFICACIONES ---
        function toggleNotifications() {
            const panel = document.getElementById("notifPanel");
            panel.classList.toggle("show");
            document.getElementById("notifBadge").style.display = "none";
        }

        async function cargarNotificaciones() {
            try {
                const response = await fetch(`${API_URL}/api/notificaciones`, { headers: getAuthHeaders() });
                if (response.ok) {
                    const notifs = await response.json();
                    const panel = document.getElementById("notifPanel");
                    const badge = document.getElementById("notifBadge");
                    
                    if (notifs.length > 0) {
                        badge.style.display = "flex";
                        badge.textContent = notifs.length;
                        panel.innerHTML = notifs.map(n => `<div class="notification-item ${n.tipo}">${n.mensaje}</div>`).join("");
                    } else {
                        badge.style.display = "none";
                        panel.innerHTML = '<div class="notification-item">No tienes notificaciones nuevas.</div>';
                    }
                }
            } catch (e) {
                console.error("Error al cargar notificaciones", e);
            }
        }

        // --- ESTADO ACTUAL ---
        async function cargarEstadoActual() {
            try {
                const response = await fetch(`${API_URL}/api/estado_actual`, { headers: getAuthHeaders() });
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById("estadoEmoji").textContent = data.emoji;
                    document.getElementById("estadoTitulo").textContent = `Hoy estás en tu Día ${data.dia}`;
                    document.getElementById("estadoFase").textContent = `Fase ${data.fase}`;
                    document.getElementById("estadoMensaje").textContent = data.mensaje;
                    setTimeout(() => {
                        document.getElementById("estadoProgreso").style.width = `${data.porcentaje}%`;
                    }, 100);
                }
            } catch (error) {
                console.error("Error al cargar estado actual:", error);
            }
        }



        // Al cargar la página
        document.addEventListener("DOMContentLoaded", () => {
            inicializarTema();
            const token = localStorage.getItem("lunita_token");
            if (token) {
                iniciarApp();
            } else {
                document.getElementById("authContainer").style.display = "flex";
                document.getElementById("dashboardContainer").style.display = "none";
                document.getElementById("topNav").style.display = "none";
            }
        });

        // 1. Verificar si la API de FastAPI responde en la raíz
        async function verificarAPI() {
            const dot = document.getElementById("statusDot");
            const text = document.getElementById("statusText");

            try {
                const response = await fetch(`${API_URL}/`);
                if (response.ok) {
                    dot.classList.add("online");
                    text.textContent = "Servidor conectado 🟢";
                } else {
                    marcarDesconectado();
                }
            } catch (error) {
                marcarDesconectado();
            }
        }

        function marcarDesconectado() {
            const dot = document.getElementById("statusDot");
            const text = document.getElementById("statusText");
            dot.classList.remove("online");
            text.innerHTML = "Servidor desconectado 🔴 <small style='color: var(--accent-salmon-hover);'>(Inicia uvicorn en local)</small>";
        }

        // 2. Mostrar alerta flotante (Toast)
        function showNotification(message, type = "success") {
            const toast = document.getElementById("toast");
            const toastEmoji = document.getElementById("toastEmoji");
            const toastMessage = document.getElementById("toastMessage");

            toastMessage.textContent = message;
            toast.className = "toast show"; // Reset classes

            if (type === "success") {
                toast.classList.add("toast-success");
                toastEmoji.textContent = "💖";
            } else {
                toast.classList.add("toast-error");
                toastEmoji.textContent = "⚠️";
            }

            setTimeout(() => {
                toast.classList.remove("show");
            }, 4000);
        }

        // 3. Agregar síntoma rápido al hacer clic en un badge
        function agregarSintoma(sintoma) {
            const inputSintomas = document.getElementById("sintomas");
            let actual = inputSintomas.value.trim();
            
            if (sintoma === 'Ninguno') {
                inputSintomas.value = 'Ninguno';
                return;
            }
            
            if (actual === 'Ninguno' || actual === '') {
                inputSintomas.value = sintoma;
            } else {
                // Evitar duplicados
                const sintomasList = actual.split(',').map(s => s.trim());
                if (!sintomasList.includes(sintoma)) {
                    inputSintomas.value = actual + ", " + sintoma;
                }
            }
        }

        // 3.1 Mostrar/Ocultar input de síntoma personalizado
        function toggleCustomSymptomInput() {
            const container = document.getElementById("customSymptomContainer");
            container.classList.toggle("show");
            if(container.classList.contains("show")) {
                document.getElementById("customSymptomInput").focus();
            }
        }

        // 3.2 Añadir síntoma personalizado
        function agregarSintomaPersonalizado() {
            const input = document.getElementById("customSymptomInput");
            const sintoma = input.value.trim();
            if (sintoma) {
                // Primera letra mayúscula
                const sintomaFormateado = sintoma.charAt(0).toUpperCase() + sintoma.slice(1).toLowerCase();
                agregarSintoma(sintomaFormateado);
                input.value = "";
                toggleCustomSymptomInput();
                showNotification(`¡'${sintomaFormateado}' añadido a tus síntomas! ✍️`, "success");
            }
        }

        // 4. Buscar consejos de bienestar (GET)
        async function buscarConsejos() {
            const diaInput = document.getElementById("consejo_dia").value;
            const faseBadgeContainer = document.getElementById("faseBadgeContainer");
            const faseName = document.getElementById("faseName");
            const consejosResults = document.getElementById("consejosResults");

            if (!diaInput || diaInput < 1) {
                showNotification("Por favor ingresa un día de ciclo válido (mayor o igual a 1).", "error");
                return;
            }

            try {
                const response = await fetch(`${API_URL}/api/consejos/${diaInput}`);
                
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || "Error en el servidor");
                }

                const data = await response.json();

                // Mostrar badge de la fase
                faseBadgeContainer.style.display = "block";
                faseName.textContent = `Fase ${data.fase} (Día ${data.dia_del_ciclo})`;
                
                // Limpiar clases y asignar la correcta para el estilo de la fase
                faseName.className = "fase-badge";
                const faseClase = "fase-" + data.fase.toLowerCase()
                                    .normalize("NFD").replace(/[\u0300-\u036f]/g, ""); // Normaliza acentos
                faseName.classList.add(faseClase);

                // Renderizar los consejos en tarjetas hermosas
                consejosResults.innerHTML = `
                    <div class="consejo-item-card">
                        <div class="consejo-icon">🥗</div>
                        <div class="consejo-content">
                            <h4>Nutrición Consciente</h4>
                            <p>${data.consejos.nutricion}</p>
                        </div>
                    </div>
                    <div class="consejo-item-card" style="animation-delay: 0.1s">
                        <div class="consejo-icon">🧘‍♀️</div>
                        <div class="consejo-content">
                            <h4>Movimiento Saludable</h4>
                            <p>${data.consejos.movimiento}</p>
                        </div>
                    </div>
                    <div class="consejo-item-card" style="animation-delay: 0.2s">
                        <div class="consejo-icon">🧠</div>
                        <div class="consejo-content">
                            <h4>Bienestar & Salud Mental</h4>
                            <p>${data.consejos.salud_mental}</p>
                        </div>
                    </div>
                `;
            } catch (error) {
                showNotification(error.message, "error");
            }
        }

        // 5. Cargar historial de registros (GET)
        let registrosGlobales = []; // Guardamos los registros en memoria para uso del modal
        
        async function cargarHistorial() {
            try {
                const response = await fetch(`${API_URL}/api/registros`, { headers: getAuthHeaders() });
                if (!response.ok) {
                    if (response.status === 401) logout();
                    throw new Error("No se pudo cargar el historial.");
                }

                registrosGlobales = await response.json();
                
                // Ya no dibujamos la lista HTML, solo actualizamos el calendario
                actualizarCalendario(registrosGlobales);

            } catch (error) {
                console.error("Error al cargar historial:", error);
            }
        }

        // 6. Guardar un nuevo registro (POST)
        async function guardarRegistro(event) {
            event.preventDefault();

            const fecha = document.getElementById("fecha").value;
            const dia_del_ciclo = parseInt(document.getElementById("dia_del_ciclo").value);
            const flujo = document.querySelector('input[name="flujo"]:checked').value;
            const animo = document.querySelector('input[name="animo"]:checked').value;
            const sintomas = document.getElementById("sintomas").value.trim();

            if (!fecha || !dia_del_ciclo || !flujo || !animo || !sintomas) {
                showNotification("Por favor completa todos los campos del formulario.", "error");
                return;
            }

            const payload = { fecha, dia_del_ciclo, flujo, animo, sintomas };

            try {
                const response = await fetch(`${API_URL}/api/registros`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        ...getAuthHeaders()
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || "Ocurrió un error al guardar.");
                }

                showNotification("¡Día guardado con éxito en tu Diario Zen! 💖", "success");
                
                // Resetear campos del formulario (mantener la fecha)
                document.getElementById("dia_del_ciclo").value = "";
                document.getElementById("sintomas").value = "";
                document.getElementById("flujo_ninguno").checked = true;
                document.getElementById("animo_feliz").checked = true;

                // Recargar historial y gráfico
                cargarHistorial();
                renderizarGrafico();

            } catch (error) {
                showNotification(error.message, "error");
            }
        }

        // 7. Eliminar un registro (DELETE)
        async function eliminarRegistro(id) {
            // Confirmación personalizada o nativa rápida (en este caso una ventana de confirmación suave)
            if (!confirm("¿Segura que deseas eliminar este día de tu diario? 🌸")) {
                return;
            }

            try {
                const response = await fetch(`${API_URL}/api/registros/${id}`, {
                    method: "DELETE",
                    headers: getAuthHeaders()
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || "No se pudo eliminar el registro.");
                }

                showNotification("Registro eliminado correctamente.", "success");
                cerrarModal(); // Si está abierto, lo cerramos
                
                // Recargar historial y gráfico
                cargarHistorial();
                renderizarGrafico();

            } catch (error) {
                showNotification(error.message, "error");
            }
        }

        // 8. Renderizar Gráfico de Evolución de Ánimo (Chart.js)
        async function renderizarGrafico() {
            try {
                const response = await fetch(`${API_URL}/api/registros`, { headers: getAuthHeaders() });
                if (!response.ok) throw new Error("No se pudieron obtener datos para el gráfico.");

                const registros = await response.json();
                const canvas = document.getElementById('graficoHistorial');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');

                // Si no hay datos, limpiamos el gráfico si existe
                if (registros.length === 0) {
                    if (miGrafico) {
                        miGrafico.destroy();
                        miGrafico = null;
                    }
                    return;
                }

                // Ordenar los registros por fecha de forma cronológica (ascendente: de más antiguo a más nuevo)
                const registrosOrdenados = [...registros].sort((a, b) => new Date(a.fecha) - new Date(b.fecha));

                // Mapear etiquetas de X (fechas formateadas como DD/MM)
                const etiquetasX = registrosOrdenados.map(reg => {
                    const partes = reg.fecha.split('-');
                    return `${partes[2]}/${partes[1]}`;
                });

                // Mapear ánimo en el eje Y (texto a números)
                const mapeoAnimo = {
                    "Feliz": 4,
                    "Normal": 3,
                    "Cansada": 2,
                    "Triste": 1,
                    "Irritable": 1
                };
                const datosY = registrosOrdenados.map(reg => mapeoAnimo[reg.animo] || 3);

                // Crear gradiente de lila/rosa semitransparente debajo de la línea
                const gradient = ctx.createLinearGradient(0, 0, 0, 220);
                gradient.addColorStop(0, 'rgba(255, 198, 255, 0.4)'); // Rosa pastel semitransparente
                gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

                // Si ya existe un gráfico previo, lo destruimos antes de crear el nuevo para evitar duplicidades
                if (miGrafico) {
                    miGrafico.destroy();
                }

                // Dibujar gráfico
                miGrafico = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: etiquetasX,
                        datasets: [{
                            label: 'Evolución del Ánimo',
                            data: datosY,
                            borderColor: '#FFAAA6', // Salmón suave
                            backgroundColor: gradient,
                            fill: true,
                            tension: 0.4, // Curvatura suave
                            borderWidth: 3,
                            pointBackgroundColor: '#B28DFF', // Lila para los puntos
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                            pointRadius: 5,
                            pointHoverRadius: 7
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false // Ocultamos la leyenda para una apariencia limpia
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const value = context.parsed.y;
                                        const labels = { 4: "😊 Feliz", 3: "😐 Normal", 2: "😴 Cansada", 1: "😢 Triste/😠 Irritable" };
                                        return `Ánimo: ${labels[value] || value}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                min: 1,
                                max: 4,
                                ticks: {
                                    stepSize: 1,
                                    callback: function(value) {
                                        const labels = { 4: "😊 Feliz", 3: "😐 Normal", 2: "😴 Cansada", 1: "😢 Triste/😠 Irritable" };
                                        return labels[value] || "";
                                    },
                                    font: {
                                        family: 'Quicksand',
                                        size: 11
                                    }
                                },
                                grid: {
                                    color: 'rgba(232, 223, 245, 0.3)'
                                }
                            },
                            x: {
                                ticks: {
                                    font: {
                                        family: 'Quicksand',
                                        size: 11
                                    }
                                },
                                grid: {
                                    display: false
                                }
                            }
                        }
                    }
                });

            } catch (error) {
                console.error("Error al renderizar el gráfico:", error);
            }
        }

        // 9. Consultar Consejera IA
        async function consultarConsejera() {
            const bubble = document.getElementById("consejeraBubble");
            const texto = document.getElementById("consejeraTexto");
            
            // Mostrar estado de carga
            bubble.style.display = "flex";
            texto.innerHTML = "<i>Consultando a los astros y tus registros... 🌙</i>";
            
            try {
                const response = await fetch(`${API_URL}/api/consejera`, { headers: getAuthHeaders() });
                if (!response.ok) throw new Error("No se pudo conectar con la consejera.");
                
                const data = await response.json();
                texto.innerHTML = data.mensaje;
            } catch (error) {
                texto.innerHTML = "Uy, hubo un problemita intentando leer las estrellas. 🌠 Intenta de nuevo más tarde.";
            }
        }

        // 10. Inicializar FullCalendar
        function inicializarCalendario() {
            const calendarEl = document.getElementById('calendarioKawaii');
            if (!calendarEl) return;
            
            miCalendario = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                locale: 'es',
                headerToolbar: {
                    left: 'prev,next',
                    center: 'title',
                    right: 'today'
                },
                buttonText: {
                    today: 'Hoy'
                },
                events: [],
                eventClick: function(info) {
                    abrirModal(info.event.extendedProps, info.event.startStr);
                }
            });
            miCalendario.render();
        }

        // --- LÓGICA DEL MODAL ---
        function abrirModal(datos, fechaStr) {
            const modal = document.getElementById("registroModal");
            
            // Formatear fecha legible
            const partes = fechaStr.split('-');
            const fechaLegible = `${partes[2]}/${partes[1]}/${partes[0]}`;
            
            document.getElementById("modalFecha").textContent = `${fechaLegible} (Día ${datos.dia_del_ciclo})`;
            
            // Icono de ánimo
            let animoEmoji = "😊";
            if (datos.animo === "Triste") animoEmoji = "😢";
            else if (datos.animo === "Irritable") animoEmoji = "😠";
            else if (datos.animo === "Cansada") animoEmoji = "😴";
            document.getElementById("modalAnimo").textContent = `${animoEmoji} ${datos.animo}`;
            
            // Icono de flujo
            let flujoIcono = "🌸";
            if (datos.flujo === "Ligero") flujoIcono = "💧";
            else if (datos.flujo === "Moderado") flujoIcono = "💦";
            else if (datos.flujo === "Abundante") flujoIcono = "🌊";
            document.getElementById("modalFlujo").textContent = `${flujoIcono} ${datos.flujo}`;
            
            document.getElementById("modalSintomas").textContent = datos.sintomas;
            
            // Botón eliminar
            document.getElementById("modalBtnEliminar").onclick = () => eliminarRegistro(datos.id);
            
            modal.classList.add("show");
        }

        function cerrarModal(event) {
            const modal = document.getElementById("registroModal");
            modal.classList.remove("show");
        }

        // 11. Actualizar eventos del calendario
        function actualizarCalendario(registros) {
            if (!miCalendario) return;
            
            const eventos = registros.map(reg => {
                let titulo = "😊";
                if (reg.animo === "Triste") titulo = "😢";
                else if (reg.animo === "Irritable") titulo = "😠";
                else if (reg.animo === "Cansada") titulo = "😴";
                
                if (reg.flujo !== "Ninguno") {
                    titulo += " 💧";
                }
                
                // Definir color de fondo basado en el ánimo o fase
                let color = "var(--accent-pink)";
                if (reg.animo === "Triste" || reg.animo === "Irritable") color = "var(--accent-salmon)";
                else if (reg.animo === "Cansada") color = "#E8DFF5";

                return {
                    title: titulo,
                    start: reg.fecha,
                    backgroundColor: color,
                    textColor: "#5C4B62",
                    allDay: true,
                    extendedProps: {
                        id: reg.id,
                        animo: reg.animo,
                        flujo: reg.flujo,
                        sintomas: reg.sintomas,
                        dia_del_ciclo: reg.dia_del_ciclo
                    }
                };
            });
            // Remover todos los eventos actuales y agregar los nuevos
            miCalendario.removeAllEvents();
            miCalendario.addEventSource(eventos);
            
            // Renderizar predicciones
            fetch(`${API_URL}/api/prediccion`, { headers: getAuthHeaders() })
                .then(res => res.json())
                .then(data => {
                    if (data.fechas && data.fechas.length > 0) {
                        const eventosPrediccion = data.fechas.map(f => ({
                            title: '✨ Periodo Estimado',
                            start: f,
                            allDay: true,
                            backgroundColor: 'rgba(255, 198, 255, 0.5)', // Rosa pastel translúcido
                            borderColor: 'transparent',
                            textColor: '#B28DFF',
                            editable: false
                        }));
                        miCalendario.addEventSource(eventosPrediccion);
                    }
                })
                .catch(err => console.error("Error al cargar predicción", err));
        }
    