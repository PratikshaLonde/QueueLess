/* =====================================================
   QUEUELESS
   MAIN JAVASCRIPT
===================================================== */


/* ================= REGISTER ================= */

function registerStudent(event) {

    event.preventDefault();

    const name = document.getElementById("reg-name").value.trim();
    const id = document.getElementById("reg-id").value.trim();
    const college = document.getElementById("reg-college").value.trim();
    const location = document.getElementById("reg-location").value.trim();

    const password =
        "QL" +
        Math.random().toString(36).substring(2, 6).toUpperCase() +
        Math.floor(10 + Math.random() * 90);

    const student = {
        name: name,
        id: id,
        college: college,
        location: location,
        password: password
    };

    localStorage.setItem(
        "queueLessStudent",
        JSON.stringify(student)
    );

    const box = document.getElementById("generated-password");

    box.style.display = "block";

    box.innerHTML = `
        <span>Your account was created successfully.</span>
        <strong>${password}</strong>
        <small>Save this password for login.</small>
    `;

    document.querySelector("form").reset();
}


/* ================= LOGIN ================= */

function loginStudent(event) {

    event.preventDefault();

    const name =
        document.getElementById("login-name").value.trim();

    const password =
        document.getElementById("login-password").value.trim();

    const savedStudent =
        JSON.parse(localStorage.getItem("queueLessStudent"));

    if (!savedStudent) {

        alert("No account found. Please register first.");

        return;
    }

    if (
        name.toLowerCase() === savedStudent.name.toLowerCase() &&
        password === savedStudent.password
    ) {

        localStorage.setItem("loggedIn", "true");

        window.location.href = "dashboard.html";

    } else {

        alert("Incorrect name or password.");

    }
}


/* ================= DASHBOARD ================= */

function loadDashboard() {

    const student =
        JSON.parse(localStorage.getItem("queueLessStudent"));

    const nameElement =
        document.getElementById("dashboard-name");

    const collegeElement =
        document.getElementById("college-info");

    if (student && nameElement) {

        nameElement.textContent = student.name;

    }

    if (student && collegeElement) {

        collegeElement.textContent =
            `${student.college} • ${student.location}`;

    }

    const serviceCollege =
        document.getElementById("service-college");

    if (student && serviceCollege) {

        serviceCollege.textContent =
            `${student.college} • ${student.location}`;

    }
}


/* ================= MENU ================= */

function toggleMenu() {

    const menu =
        document.getElementById("dropdown-menu");

    if (menu) {

        menu.classList.toggle("show");

    }
}


/* ================= LOGOUT ================= */

function logoutStudent() {

    localStorage.removeItem("loggedIn");

    window.location.href = "index.html";
}


/* ================= BUTTON EFFECT ================= */

function openCard(button, page) {

    button.classList.add("clicked");

    setTimeout(function() {

        window.location.href = page;

    }, 250);
}


/* ================= QUEUE DATA ================= */

const defaultQueues = {

    "College Canteen": {
        queue: 18,
        serviceTime: 2
    },

    "Admin Office": {
        queue: 12,
        serviceTime: 3
    },

    "Computer Lab": {
        queue: 5,
        serviceTime: 5
    },

    "Library": {
        queue: 8,
        serviceTime: 3
    },

    "Student Office": {
        queue: 9,
        serviceTime: 4
    },

    "Accounts Office": {
        queue: 7,
        serviceTime: 4
    }

};


/* ================= INITIALIZE QUEUES ================= */

function initializeQueues() {

    let saved =
        JSON.parse(localStorage.getItem("liveQueues"));

    if (!saved) {

        saved = {};

        Object.keys(defaultQueues).forEach(function(service) {

            saved[service] = {
                queue: defaultQueues[service].queue,
                serviceTime: defaultQueues[service].serviceTime
            };

        });

        localStorage.setItem(
            "liveQueues",
            JSON.stringify(saved)
        );
    }

    return saved;
}


/* ================= GET MY QUEUES ================= */

function getMyQueues() {

    try {

        return JSON.parse(
            localStorage.getItem("myQueues")
        ) || [];

    } catch {

        return [];

    }
}


/* ================= SAVE MY QUEUES ================= */

function saveMyQueues(queues) {

    localStorage.setItem(
        "myQueues",
        JSON.stringify(queues)
    );
}


/* ================= JOIN QUEUE ================= */

function joinQueue(button) {

    const card =
        button.closest(".service-card");

    const serviceName =
        card.dataset.service;

    const queues =
        initializeQueues();

    const myQueues =
        getMyQueues();

    const alreadyJoined =
        myQueues.some(function(item) {

            return item.service === serviceName;

        });

    if (alreadyJoined) {

        showJoinMessage(
            `You already joined ${serviceName}.`
        );

        return;
    }


    const currentQueue =
        queues[serviceName].queue;

    const serviceTime =
        queues[serviceName].serviceTime;


    const myNumber =
        currentQueue + 1;


    /*
       For demo:
       1 person is served every serviceTime minutes.

       The countdown uses seconds internally.
    */

    const estimatedSeconds =
        myNumber * serviceTime * 60;


    const newQueue = {

        service: serviceName,

        number: myNumber,

        joinedAt: Date.now(),

        targetTime:
            Date.now() + estimatedSeconds * 1000,

        serviceTime: serviceTime,

        warningShown: false,

        notified: false

    };


    myQueues.push(newQueue);

    saveMyQueues(myQueues);


    /* Increase service queue */

    queues[serviceName].queue =
        currentQueue + 1;

    localStorage.setItem(
        "liveQueues",
        JSON.stringify(queues)
    );


    /* Update card */

    const count =
        card.querySelector(".queue-count");

    const emptyTime =
        card.querySelector(".empty-time");

    if (count) {

        count.textContent =
            queues[serviceName].queue;

    }

    if (emptyTime) {

        emptyTime.textContent =
            (
                queues[serviceName].queue *
                serviceTime
            ) + " min";

    }


    button.textContent = "JOINED";

    button.classList.add("joined");

    button.disabled = true;


    showJoinMessage(
        `${serviceName} joined successfully. Your number is #${myNumber}`
    );


    startQueueSystem();
}


/* ================= LEAVE QUEUE ================= */

function leaveQueue(serviceName) {

    let myQueues =
        getMyQueues();

    myQueues =
        myQueues.filter(function(item) {

            return item.service !== serviceName;

        });

    saveMyQueues(myQueues);


    showJoinMessage(
        `You left ${serviceName}.`
    );


    renderMyQueues();
}


/* ================= FORMAT TIME ================= */

function formatTime(totalSeconds) {

    totalSeconds =
        Math.max(0, Math.floor(totalSeconds));

    const hours =
        Math.floor(totalSeconds / 3600);

    const minutes =
        Math.floor(
            (totalSeconds % 3600) / 60
        );

    const seconds =
        totalSeconds % 60;


    return String(hours).padStart(2, "0") +
        ":" +
        String(minutes).padStart(2, "0") +
        ":" +
        String(seconds).padStart(2, "0");
}


/* ================= MY QUEUE PAGE ================= */

function renderMyQueues() {

    const container =
        document.getElementById(
            "my-queues-container"
        );

    const empty =
        document.getElementById("no-queues");


    if (!container) return;


    const myQueues =
        getMyQueues();


    container.innerHTML = "";


    if (myQueues.length === 0) {

        if (empty) {
            empty.style.display = "block";
        }

        return;

    }


    if (empty) {

        empty.style.display = "none";

    }


    myQueues.forEach(function(item, index) {

        const remaining =
            Math.max(
                0,
                Math.floor(
                    (item.targetTime - Date.now()) / 1000
                )
            );


        const card =
            document.createElement("div");

        card.className = "my-queue-card";


        card.innerHTML = `

            <div>
                <h2>${item.service}</h2>
                <p>Live queue tracking</p>
            </div>

            <div>
                <p>Your Number</p>
                <div class="ticket-number">
                    #${item.number}
                </div>
            </div>

            <div>
                <p>Estimated Waiting Time</p>
                <div
                    class="live-time"
                    data-index="${index}">
                    ${formatTime(remaining)}
                </div>
            </div>

            <button
                class="leave-button"
                onclick="leaveQueue('${item.service}')">
                LEAVE
            </button>

        `;


        container.appendChild(card);

    });

}


/* ================= LIVE COUNTDOWN ================= */

function updateMyQueueTimers() {

    const myQueues =
        getMyQueues();


    myQueues.forEach(function(item, index) {

        const remaining =
            Math.max(
                0,
                Math.floor(
                    (item.targetTime - Date.now()) / 1000
                )
            );


        const timer =
            document.querySelector(
                `.live-time[data-index="${index}"]`
            );


        if (timer) {

            timer.textContent =
                formatTime(remaining);

        }


        /* 2 MINUTE WARNING */

        if (
            remaining <= 120 &&
            remaining > 0 &&
            !item.warningShown
        ) {

            showNotification(
                `Your ${item.service} queue is coming up in 2 minutes!`
            );

            playNotificationSound();

            item.warningShown = true;

            saveMyQueues(myQueues);

        }


        /* YOUR TURN */

        if (
            remaining === 0 &&
            !item.notified
        ) {

            showNotification(
                `🎉 Your number #${item.number} has arrived at ${item.service}!`
            );

            playNotificationSound();

            item.notified = true;

            saveMyQueues(myQueues);

        }

    });

}


/* ================= QUEUE NUMBERS DECREASE ================= */

function updateLiveQueues() {

    let queues =
        initializeQueues();


    Object.keys(queues).forEach(function(service) {

        if (queues[service].queue > 0) {

            queues[service].queue--;

        }

    });


    localStorage.setItem(
        "liveQueues",
        JSON.stringify(queues)
    );


    updateServiceCards();

}


/* ================= SERVICE CARD UPDATE ================= */

function updateServiceCards() {

    const cards =
        document.querySelectorAll(
            ".service-card"
        );

    const queues =
        initializeQueues();


    cards.forEach(function(card) {

        const service =
            card.dataset.service;

        if (!queues[service]) return;


        const count =
            card.querySelector(".queue-count");

        const emptyTime =
            card.querySelector(".empty-time");


        if (count) {

            count.textContent =
                queues[service].queue;

        }


        if (emptyTime) {

            emptyTime.textContent =
                (
                    queues[service].queue *
                    queues[service].serviceTime
                ) + " min";

        }

    });

}


/* ================= NOTIFICATION ================= */

function showNotification(message) {

    const notification =
        document.createElement("div");

    notification.className =
        "queue-notification";


    notification.innerHTML = `

        <div style="font-size:24px">
            🔔
        </div>

        <div>
            <strong>QueueLess</strong>
            <p>${message}</p>
        </div>

    `;


    document.body.appendChild(
        notification
    );


    setTimeout(function() {

        notification.classList.add("show");

    }, 50);


    setTimeout(function() {

        notification.classList.remove("show");

        setTimeout(function() {

            notification.remove();

        }, 500);

    }, 6000);

}


/* ================= NOTIFICATION SOUND ================= */

function playNotificationSound() {

    try {

        const audioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();


        const oscillator =
            audioContext.createOscillator();

        const gain =
            audioContext.createGain();


        oscillator.connect(gain);

        gain.connect(
            audioContext.destination
        );


        oscillator.frequency.value = 850;

        gain.gain.setValueAtTime(
            0.0001,
            audioContext.currentTime
        );

        gain.gain.exponentialRampToValueAtTime(
            0.15,
            audioContext.currentTime + 0.02
        );

        gain.gain.exponentialRampToValueAtTime(
            0.0001,
            audioContext.currentTime + 0.25
        );


        oscillator.start();

        oscillator.stop(
            audioContext.currentTime + 0.25
        );

    } catch (error) {

        console.log("Sound unavailable");

    }

}


/* ================= MESSAGE ================= */

function showJoinMessage(message) {

    const box =
        document.getElementById(
            "join-message"
        );


    if (!box) return;


    box.textContent =
        message;


    box.classList.add("show");


    setTimeout(function() {

        box.classList.remove("show");

    }, 3500);

}


/* ================= FEEDBACK ================= */

function sendFeedback() {

    const feedback =
        document.getElementById("feedback").value.trim();

    const result =
        document.getElementById(
            "feedback-result"
        );


    if (!feedback) {

        result.textContent =
            "Please write some feedback.";

        return;

    }


    localStorage.setItem(
        "queueLessFeedback",
        feedback
    );


    result.textContent =
        "😊 Thank you! Your feedback was submitted.";

    document.getElementById(
        "feedback"
    ).value = "";

}


/* ================= QUEUE SYSTEM ================= */

let queueIntervalStarted = false;

function startQueueSystem() {

    if (queueIntervalStarted) return;

    queueIntervalStarted = true;


    /*
       DEMO MODE

       Every 30 seconds one person leaves
       each queue.

       For a real college deployment this
       should be controlled by an admin/backend.
    */

    setInterval(function() {

        updateLiveQueues();

    }, 30000);


    setInterval(function() {

        updateMyQueueTimers();

    }, 1000);

}


/* ================= PAGE START ================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        initializeQueues();

        loadDashboard();

        updateServiceCards();

        renderMyQueues();

        startQueueSystem();

        updateMyQueueTimers();

    }
);