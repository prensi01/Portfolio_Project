// ======================
// Close Menu on Link Click
// ======================
const navbar = document.querySelector(".navbar");
document.querySelectorAll('.navbar a').forEach(link => {
    link.addEventListener('click', () => {
        if (navbar) {
            navbar.classList.remove('active');
        }
    });
});


// ======================
// Dark / Light Mode Toggle
// ======================
const themeToggle = document.getElementById("theme-toggle");

if (themeToggle) {

    // Page load hone par saved theme apply karo
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "light") {
        document.body.classList.add("light-mode");
        themeToggle.querySelector("i").classList.replace("fa-moon", "fa-sun");
        themeToggle.querySelector("span").textContent = "Light";
    }

    themeToggle.addEventListener("click", () => {

        document.body.classList.toggle("light-mode");

        const icon = themeToggle.querySelector("i");
        const text = themeToggle.querySelector("span");

        if (document.body.classList.contains("light-mode")) {

            icon.classList.replace("fa-moon", "fa-sun");
            text.textContent = "Light";

            localStorage.setItem("theme", "light");

        } else {

            icon.classList.replace("fa-sun", "fa-moon");
            text.textContent = "Dark";

            localStorage.setItem("theme", "dark");

        }

    });

}
// ======================
// Navbar Active Section
// ======================
let sections = document.querySelectorAll('section');
let navLinks = document.querySelectorAll('.navbar a');
let sideLinks = document.querySelectorAll('.sidebar a');

window.addEventListener("scroll", () => {

    let current = '';

    sections.forEach(section => {
        const sectionTop = section.offsetTop - 150;

        if (window.scrollY >= sectionTop) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');

        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });

    sideLinks.forEach(link => {
        link.classList.remove('active');

        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });

});


// ======================
// Header Background on Scroll
// ======================

window.addEventListener('scroll', () => {

    const header = document.querySelector('.header');

    if (header) {

        if (window.scrollY > 100) {
            header.style.background = 'rgba(0,0,0,0.8)';
        } else {
            header.style.background = 'rgba(0,0,0,0.4)';
        }

    }

});


// ======================
// Scroll Reveal Animation
// ======================

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if(entry.isIntersecting){
            entry.target.classList.add("show");
        }
    });
});
document.querySelectorAll(
    '.home-content, .home-img, .about-content, .skill, .project-box, .contact form'
).forEach(el => {
    observer.observe(el);
});


// ======================
// Typing Effect
// ======================
const words = [
  "Data Analyst",
  "Python Developer",
  "SQL Enthusiast",
  "Power BI Developer",
  "Excel Expert",
  "Problem Solver",
  "Business Intelligence Learner"
];

let i = 0;
let j = 0;
let currentWord = "";
let isDeleting = false;

function typeEffect(){
    currentWord = words[i];

    if(!isDeleting){
        document.getElementById("typing-text").textContent =
        currentWord.substring(0,j++);
    }else{
        document.getElementById("typing-text").textContent =
        currentWord.substring(0,j--);
    }

    let speed = isDeleting ? 80 : 120;

    if(!isDeleting && j === currentWord.length + 1){
        isDeleting = true;
        speed = 1500;
    }

    if(isDeleting && j === 0){
        isDeleting = false;
        i = (i + 1) % words.length;
    }

    setTimeout(typeEffect,speed);
}

if (document.getElementById("typing-text")) {
    typeEffect();
}

// ======================
// Back To Top Smooth Scroll
// ======================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {

    anchor.addEventListener('click', function (e) {

        e.preventDefault();

        const target = document.querySelector(
            this.getAttribute('href')
        );

        if (target) {

            target.scrollIntoView({
                behavior: 'smooth'
            });

        }

    });

});


// ======================
// Console Welcome Message
// ======================

console.log(
    "Portfolio Website Loaded Successfully 🚀"
);

let cursorEnabled = false;
let cursor;

function initCursor() {
    if (cursorEnabled) return;

    cursor = document.createElement("div");
    cursor.className = "custom-cursor";

    cursor.style.position = "fixed";
    cursor.style.width = "18px";
    cursor.style.height = "18px";
    cursor.style.borderRadius = "50%";
    cursor.style.pointerEvents = "none";
    cursor.style.zIndex = "9999";
    cursor.style.transform = "translate(-50%, -50%)";

    document.body.appendChild(cursor);

    document.addEventListener("mousemove", moveCursor);

    cursorEnabled = true;
}

function moveCursor(e) {
    if (!cursor) return;
    cursor.style.left = e.clientX + "px";
    cursor.style.top = e.clientY + "px";
}

function destroyCursor() {
    if (!cursorEnabled) return;

    document.removeEventListener("mousemove", moveCursor);
    cursor.remove();

    cursor = null;
    cursorEnabled = false;
}

function checkDevice() {
    if (window.innerWidth > 768) {
        initCursor();
    } else {
        destroyCursor();
    }
}

window.addEventListener("resize", checkDevice);
checkDevice();

let modal = document.getElementById("project-modal");
let title = document.getElementById("modal-title");
let desc = document.getElementById("modal-desc");
let closeBtn = document.querySelector(".close");

document.querySelectorAll(".project-box").forEach(box => {
    box.addEventListener("click", () => {
        title.textContent = box.querySelector("h2").textContent;
        desc.textContent =
box.querySelector(".desc").textContent;
        modal.style.display = "flex";
    });
});
if (closeBtn) {
    closeBtn.onclick = () => {
        modal.style.display = "none";
    };
}
window.addEventListener("click", (e) => {
    if (modal && e.target === modal) {
        modal.style.display = "none";
    }
});
const canvas = document.getElementById("bg");

if (canvas && typeof THREE !== "undefined") {

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );

    const renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        alpha: true,
        antialias: true
    });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    const geometry = new THREE.SphereGeometry(1.3, 24, 24);
    const material = new THREE.MeshBasicMaterial({
    color: 0x005577,   // Dark Blue
    wireframe: true,
    transparent: true,
    opacity: 0.65
});

    const sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);

    camera.position.z = 4;
    function animate() {
    requestAnimationFrame(animate);

    sphere.rotation.y += 0.010;
    sphere.rotation.x += 0.005;

    renderer.render(scene, camera);
}

    animate();

    window.addEventListener("resize", () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}
function openMenu() {
    document.getElementById("mySidebar").style.width = "250px";
}

function closeMenu() {
    document.getElementById("mySidebar").style.width = "0";
}
const sidebarLinks = document.querySelectorAll(".sidebar a");
sidebarLinks.forEach(link => {
    link.addEventListener("click", function() {

        sidebarLinks.forEach(item => {
            item.classList.remove("active");
        });

        this.classList.add("active");

        // Sidebar automatically close
        closeMenu();
    });
});
if (typeof particlesJS !== "undefined") {
particlesJS("particles-js", {
    particles: {
        number: {
            value: 80,
            density: {
                enable: true,
                value_area: 1000
            }
        },
        color: {
            value: "#00abf0"
        },
        shape: {
            type: "circle"
        },
        opacity: {
            value: 0.25
        },
        size: {
            value: 3
        },
        line_linked: {
            enable: true,
            distance: 150,
            color: "#00abf0",
            opacity: 0.2,
            width: 1
        },
        move: {
            enable: true,
            speed: 1.5,
            out_mode: "bounce"
        }
    },
    interactivity: {
        detect_on: "canvas",
        events: {
            onhover: {
                enable: true,
                mode: "grab"
            },
            resize: true
        },
        modes: {
            grab: {
                distance: 180,
                line_linked: {
                    opacity: 0.5
                }
            }
        }
    },
    retina_detect: true
});
}