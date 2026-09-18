(() => {
  const form = document.querySelector("#assistant-form");
  if (!form) return;

  const messages = document.querySelector("#assistant-messages");
  const input = document.querySelector("#assistant-input");
  const send = document.querySelector("#assistant-send");
  const upload = document.querySelector(".assistant-upload");
  const photos = document.querySelector("#assistant-photos");
  const photoCount = document.querySelector("#assistant-photo-count");
  const photosDone = document.querySelector("#assistant-photos-done");
  const skipPhoto = document.querySelector("#assistant-skip-photo");
  const arStart = document.querySelector("#assistant-ar-start");
  const arScreen = document.querySelector("#ar-measurement");
  const arCanvas = document.querySelector("#ar-canvas");
  const arStatus = document.querySelector("#ar-status");
  const arClose = document.querySelector("#ar-close");
  const arActions = document.querySelector("#ar-result-actions");
  const arReset = document.querySelector("#ar-reset");
  const a4Start = document.querySelector("#assistant-a4-start");
  const a4Screen = document.querySelector("#a4-measurement");
  const a4Close = document.querySelector("#a4-close");
  const a4Photo = document.querySelector("#a4-photo");
  const a4Canvas = document.querySelector("#a4-canvas");
  const a4Status = document.querySelector("#a4-status");
  const a4Actions = document.querySelector("#a4-actions");
  const a4Reset = document.querySelector("#a4-reset");
  const a4Camera = document.querySelector("#a4-camera");
  const a4Video = document.querySelector("#a4-video");
  const a4Capture = document.querySelector("#a4-capture");
  const scanStart = document.querySelector("#assistant-scan-start");
  const scanScreen = document.querySelector("#project-scan");
  const scanVideo = document.querySelector("#scan-video");
  const scanPrompt = document.querySelector("#scan-prompt");
  const scanStatus = document.querySelector("#scan-status");
  const scanCapture = document.querySelector("#scan-capture");
  const scanClose = document.querySelector("#scan-close");
  const data = {};
  const projectFiles = [];
  const questions = [
    ["project", "היי, אני OrPro Assist 👋 ספרו לי במילים שלכם: מה תרצו לעשות בבית?", "למשל: אני רוצה פרגולה בחצר, יש נזילה במטבח..."],
    ["location", "מעולה. באיזו עיר או אזור נמצא הפרויקט?", "עיר או אזור"],
    ["measurements", "יש לכם מידות משוערות? אפשר לכתוב למשל: 4 על 3, גובה 2.5. אם אין — כתבו 'אין לי'.", "כתבו מידות משוערות או 'אין לי'"],
    ["photos", "מצוין. עכשיו אפשר לצרף תמונות של השטח. הן יעזרו לבעל העסק להבין את העבודה.", ""],
    ["name", "איך קוראים לכם?", "שם מלא"],
    ["phone", "מה מספר הטלפון לחזרה?", "050-1234567"],
    ["email", "ולסיום, אימייל לקבלת ההצעות? אפשר לכתוב 'דלג'.", "name@example.com"],
  ];
  let step = 0;

  const addMessage = (text, type) => {
    const bubble = document.createElement("div");
    bubble.className = `assistant-bubble ${type}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
  };
  const ask = () => {
    const [, question, placeholder] = questions[step];
    addMessage(question, "bot");
    input.placeholder = placeholder;
    const photoStep = questions[step][0] === "photos";
    upload.hidden = !photoStep;
    input.hidden = photoStep;
    send.hidden = photoStep;
    if (photoStep) {
      photos.focus();
    } else {
      input.focus();
    }
  };
  const parseMeasurements = (value) => {
    const values = value.replace(/,/g, ".").match(/\d+(?:\.\d+)?/g) || [];
    data.width = values[0] || "";
    data.length = values[1] || "";
    data.height = values[2] || "";
  };
  const categorySlug = (value) => {
    const text = value.toLowerCase();
    if (/פרגול|דק|הצלל/.test(text)) return "pergolas";
    if (/מטבח|ארון|נגר/.test(text)) return "kitchens";
    if (/נזיל|צנר|ברז|סתימ|ביוב|אינסטל/.test(text)) return "plumbing";
    if (/חשמל|שקע|תאור|לוח/.test(text)) return "electricity";
    return "renovations";
  };
  const finish = () => {
    form.service_type.value = data.project;
    form.description.value = data.project;
    form.city.value = data.location;
    form.address.value = data.location;
    form.estimated_width.value = data.width;
    form.estimated_length.value = data.length;
    form.estimated_height.value = data.height;
    form.name.value = data.name;
    form.phone.value = data.phone;
    form.email.value = data.email === "דלג" ? "" : data.email;
    form.action = `/שירותים/${categorySlug(data.project)}/`;
    addMessage("תודה! אני שולח עכשיו את הפרטים לבעלי העסק המתאימים.", "bot");
    setTimeout(() => form.submit(), 700);
  };
  const answer = () => {
    const value = input.value.trim();
    if (!value) return;
    if (questions[step][0] === "phone" && value.replace(/\D/g, "").length < 8) {
      addMessage("נראה שחסר חלק מהמספר. אפשר לכתוב שוב טלפון מלא?", "bot");
      return;
    }
    data[questions[step][0]] = value;
    if (questions[step][0] === "measurements") parseMeasurements(value);
    addMessage(value, "customer");
    input.value = "";
    step += 1;
    if (step < questions.length) ask(); else finish();
  };
  send.addEventListener("click", answer);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") { event.preventDefault(); answer(); }
  });
  photos.addEventListener("change", () => {
    [...photos.files].forEach((image) => projectFiles.push(image));
    const files = new DataTransfer();
    projectFiles.forEach((image) => files.items.add(image));
    photos.files = files.files;
    const count = projectFiles.length;
    data.photos = count;
    photoCount.textContent = `נוספו ${count} תמונות פרויקט. אפשר להוסיף עוד או להמשיך.`;
  });
  photosDone.addEventListener("click", () => {
    const count = projectFiles.length;
    addMessage(count ? `צירפתי ${count} תמונות של הפרויקט` : "סיימתי בלי תמונות פרויקט", "customer");
    step += 1;
    ask();
  });
  skipPhoto.addEventListener("click", () => {
    addMessage("אין לי תמונות כרגע", "customer");
    step += 1;
    ask();
  });

  let arSession;
  let arPoints = [];
  let arPosition;
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
  const stopAR = async () => {
    if (arSession) await arSession.end();
    arSession = null;
    arScreen.hidden = true;
  };
  const resetAR = () => {
    arPoints = [];
    arActions.hidden = true;
    arStatus.textContent = "כוונו למשטח ולחצו על שתי נקודות למדידה.";
  };
  const startAR = async () => {
    if (!navigator.xr) {
      addMessage("מדידת AR אינה נתמכת בדפדפן הזה. אפשר לצלם עם דף A4 ולהזין מידה משוערת.", "bot");
      return;
    }
    try {
      const supported = await navigator.xr.isSessionSupported("immersive-ar");
      if (!supported) throw new Error("unsupported");
      arScreen.hidden = false;
      const gl = arCanvas.getContext("webgl", { xrCompatible: true });
      arSession = await navigator.xr.requestSession("immersive-ar", { requiredFeatures: ["hit-test", "local-floor"] });
      await gl.makeXRCompatible();
      arSession.updateRenderState({ baseLayer: new XRWebGLLayer(arSession, gl) });
      const referenceSpace = await arSession.requestReferenceSpace("local-floor");
      const viewerSpace = await arSession.requestReferenceSpace("viewer");
      const hitTestSource = await arSession.requestHitTestSource({ space: viewerSpace });
      arSession.addEventListener("end", () => { arScreen.hidden = true; arSession = null; });
      arSession.addEventListener("select", () => {
        if (!arPosition || arPoints.length === 2) return;
        arPoints.push({ ...arPosition });
        if (arPoints.length === 1) arStatus.textContent = "נקודה ראשונה נשמרה. לחצו על נקודת הסיום.";
        if (arPoints.length === 2) {
          const meters = distance(arPoints[0], arPoints[1]).toFixed(2);
          arStatus.textContent = `נמדדו ${meters} מטרים. לאיזו מידה לשמור?`;
          arActions.hidden = false;
        }
      });
      const frameLoop = (_, frame) => {
        arSession.requestAnimationFrame(frameLoop);
        const baseLayer = arSession.renderState.baseLayer;
        gl.bindFramebuffer(gl.FRAMEBUFFER, baseLayer.framebuffer);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        const hits = frame.getHitTestResults(hitTestSource);
        if (hits.length) {
          const pose = hits[0].getPose(referenceSpace);
          arPosition = pose.transform.position;
        }
      };
      arSession.requestAnimationFrame(frameLoop);
    } catch (_) {
      arScreen.hidden = true;
      addMessage("לא ניתן לפתוח AR במכשיר הזה. נסו Chrome במכשיר Android או השתמשו בצילום עם דף A4.", "bot");
    }
  };
  arStart.addEventListener("click", startAR);
  arClose.addEventListener("click", stopAR);
  arReset.addEventListener("click", resetAR);
  document.querySelectorAll("[data-ar-dimension]").forEach((button) => {
    button.addEventListener("click", async () => {
      const meters = distance(arPoints[0], arPoints[1]).toFixed(2);
      data[button.dataset.arDimension] = meters;
      addMessage(`מדידת AR נשמרה: ${button.dataset.arDimension === "width" ? "רוחב" : "אורך"} ${meters} מ׳`, "customer");
      await stopAR();
    });
  });

  let a4Points = [];
  let measurePoints = [];
  let a4Homography;
  let a4Image;
  let cameraStream;
  let scanStream;
  let scanIndex = 0;
  const addMeasurementPhoto = (file) => {
    projectFiles.push(file);
    const files = new DataTransfer();
    projectFiles.forEach((image) => files.items.add(image));
    photos.files = files.files;
    photoCount.textContent = `נוספו ${projectFiles.length} תמונות, כולל צילום המדידה.`;
  };
  const stopCamera = () => {
    if (cameraStream) cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  };
  const stopScan = () => {
    if (scanStream) scanStream.getTracks().forEach((track) => track.stop());
    scanStream = null;
    scanScreen.hidden = true;
  };
  const loadA4Image = (source, file) => {
    if (file) addMeasurementPhoto(file);
    a4Image = new Image();
    a4Image.onload = () => { resetA4(); a4Camera.hidden = true; };
    a4Image.src = source;
    a4Canvas.hidden = false;
  };
  const solve = (matrix, values) => {
    const size = values.length;
    const augmented = matrix.map((row, index) => [...row, values[index]]);
    for (let pivot = 0; pivot < size; pivot += 1) {
      let best = pivot;
      for (let row = pivot + 1; row < size; row += 1) if (Math.abs(augmented[row][pivot]) > Math.abs(augmented[best][pivot])) best = row;
      [augmented[pivot], augmented[best]] = [augmented[best], augmented[pivot]];
      const divisor = augmented[pivot][pivot];
      if (Math.abs(divisor) < 0.000001) return null;
      for (let col = pivot; col <= size; col += 1) augmented[pivot][col] /= divisor;
      for (let row = 0; row < size; row += 1) {
        if (row === pivot) continue;
        const factor = augmented[row][pivot];
        for (let col = pivot; col <= size; col += 1) augmented[row][col] -= factor * augmented[pivot][col];
      }
    }
    return augmented.map((row) => row[size]);
  };
  const makeHomography = (source) => {
    const target = [[0.21, 0.297], [0, 0.297], [0, 0], [0.21, 0]];
    const matrix = [];
    const values = [];
    source.forEach(([x, y], index) => {
      const [X, Y] = target[index];
      matrix.push([x, y, 1, 0, 0, 0, -X * x, -X * y]); values.push(X);
      matrix.push([0, 0, 0, x, y, 1, -Y * x, -Y * y]); values.push(Y);
    });
    return solve(matrix, values);
  };
  const mapA4Point = ([x, y]) => {
    const h = a4Homography;
    const denominator = h[6] * x + h[7] * y + 1;
    return [(h[0] * x + h[1] * y + h[2]) / denominator, (h[3] * x + h[4] * y + h[5]) / denominator];
  };
  const drawA4 = () => {
    if (!a4Image) return;
    const context = a4Canvas.getContext("2d");
    const ratio = Math.min(1, 700 / a4Image.naturalWidth);
    a4Canvas.width = Math.round(a4Image.naturalWidth * ratio);
    a4Canvas.height = Math.round(a4Image.naturalHeight * ratio);
    context.drawImage(a4Image, 0, 0, a4Canvas.width, a4Canvas.height);
    context.lineWidth = 4;
    [...a4Points, ...measurePoints].forEach(([x, y], index) => {
      context.beginPath(); context.arc(x, y, 8, 0, Math.PI * 2);
      context.fillStyle = index < 4 ? "#edb75c" : "#6be19a"; context.fill();
    });
    if (a4Points.length === 4) {
      context.beginPath(); a4Points.forEach(([x, y], index) => index ? context.lineTo(x, y) : context.moveTo(x, y)); context.closePath(); context.strokeStyle = "#edb75c"; context.stroke();
    }
    if (measurePoints.length === 2) {
      context.beginPath(); context.moveTo(...measurePoints[0]); context.lineTo(...measurePoints[1]); context.strokeStyle = "#6be19a"; context.stroke();
    }
  };
  const resetA4 = () => {
    a4Points = []; measurePoints = []; a4Homography = null; a4Actions.hidden = true;
    a4Status.textContent = "סמנו את ארבע פינות דף ה־A4 לפי הסדר: ימין־למטה, שמאל־למטה, שמאל־למעלה, ימין־למעלה.";
    drawA4();
  };
  a4Start.addEventListener("click", async () => {
    a4Screen.hidden = false;
    a4Camera.hidden = false;
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      a4Video.srcObject = cameraStream;
      a4Status.textContent = "כוונו את המצלמה כך שדף ה־A4 והשטח שאותו מודדים יופיעו בתמונה, ואז צלמו.";
    } catch (_) {
      a4Camera.hidden = true;
      a4Status.textContent = "אין גישה למצלמה. אפשר לבחור תמונה קיימת או לאשר הרשאת מצלמה בדפדפן.";
    }
  });
  a4Close.addEventListener("click", () => { stopCamera(); a4Screen.hidden = true; });
  a4Reset.addEventListener("click", resetA4);
  a4Photo.addEventListener("change", () => {
    const file = a4Photo.files[0]; if (!file) return;
    stopCamera();
    loadA4Image(URL.createObjectURL(file), file);
  });
  a4Capture.addEventListener("click", () => {
    if (!a4Video.videoWidth) return;
    const snapshot = document.createElement("canvas");
    snapshot.width = a4Video.videoWidth; snapshot.height = a4Video.videoHeight;
    snapshot.getContext("2d").drawImage(a4Video, 0, 0);
    snapshot.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], `measurement-${Date.now()}.jpg`, { type: "image/jpeg" });
      stopCamera();
      loadA4Image(URL.createObjectURL(file), file);
    }, "image/jpeg", 0.92);
  });
  const scanSteps = ["תמונה כללית של כל השטח", "צילום מצד ימין של אזור העבודה", "צילום מהצד הנגדי כדי להבין עומק", "צילום מקרוב של הפרט החשוב או התקלה"];
  scanStart.addEventListener("click", async () => {
    scanIndex = 0;
    scanScreen.hidden = false;
    scanPrompt.textContent = `צילום 1 מתוך 4: ${scanSteps[0]}`;
    try {
      scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      scanVideo.srcObject = scanStream;
    } catch (_) {
      stopScan();
      addMessage("לא ניתן לפתוח מצלמה לסריקה. אפשר לצרף תמונות רגילות מהטלפון.", "bot");
    }
  });
  scanClose.addEventListener("click", stopScan);
  scanCapture.addEventListener("click", () => {
    if (!scanVideo.videoWidth) return;
    const snapshot = document.createElement("canvas");
    snapshot.width = scanVideo.videoWidth; snapshot.height = scanVideo.videoHeight;
    snapshot.getContext("2d").drawImage(scanVideo, 0, 0);
    snapshot.toBlob((blob) => {
      if (!blob) return;
      addMeasurementPhoto(new File([blob], `project-scan-${Date.now()}-${scanIndex + 1}.jpg`, { type: "image/jpeg" }));
      scanIndex += 1;
      if (scanIndex === scanSteps.length) {
        stopScan();
        addMessage("השלמתי סריקה מודרכת של הפרויקט עם 4 תמונות", "customer");
      } else {
        scanStatus.textContent = `התמונה נשמרה. ממשיכים לצילום ${scanIndex + 1}.`;
        scanPrompt.textContent = `צילום ${scanIndex + 1} מתוך 4: ${scanSteps[scanIndex]}`;
      }
    }, "image/jpeg", 0.92);
  });
  a4Canvas.addEventListener("click", (event) => {
    if (!a4Image) return;
    const box = a4Canvas.getBoundingClientRect();
    const point = [(event.clientX - box.left) * (a4Canvas.width / box.width), (event.clientY - box.top) * (a4Canvas.height / box.height)];
    if (a4Points.length < 4) {
      a4Points.push(point);
      if (a4Points.length === 4) {
        a4Homography = makeHomography(a4Points);
        if (!a4Homography) { resetA4(); return; }
        a4Status.textContent = "עכשיו לחצו על נקודת ההתחלה ועל נקודת הסיום של מה שתרצו למדוד.";
      }
    } else if (measurePoints.length < 2) {
      measurePoints.push(point);
      if (measurePoints.length === 2) {
        const start = mapA4Point(measurePoints[0]); const end = mapA4Point(measurePoints[1]);
        const meters = Math.hypot(start[0] - end[0], start[1] - end[1]).toFixed(2);
        a4Status.textContent = `נמדדו ${meters} מטרים. לאיזו מידה לשמור?`;
        a4Actions.dataset.meters = meters; a4Actions.hidden = false;
      }
    }
    drawA4();
  });
  document.querySelectorAll("[data-a4-dimension]").forEach((button) => {
    button.addEventListener("click", () => {
      const meters = a4Actions.dataset.meters;
      data[button.dataset.a4Dimension] = meters;
      addMessage(`מדידה מצילום A4 נשמרה: ${button.dataset.a4Dimension === "width" ? "רוחב" : "אורך"} ${meters} מ׳`, "customer");
      a4Screen.hidden = true;
      if (questions[step][0] === "photos") addMessage("צירפתי גם צילום מדידה עם דף A4", "customer");
    });
  });
  ask();
})();
