(() => {
  const form = document.querySelector("#assistant-form");
  if (!form) return;
  const config = JSON.parse(document.querySelector("#assistant-config").textContent);
  const messages = document.querySelector("#assistant-messages");
  const input = document.querySelector("#assistant-input");
  const send = document.querySelector("#assistant-send");
  const compose = document.querySelector(".assistant-compose");
  const upload = document.querySelector(".assistant-upload");
  const photos = document.querySelector("#assistant-photos");
  const photoCount = document.querySelector("#assistant-photo-count");
  const photosDone = document.querySelector("#assistant-photos-done");
  const photoPreview = document.querySelector("#assistant-photo-preview");
  const skipPhoto = document.querySelector("#assistant-skip-photo");
  const review = document.querySelector("#assistant-review");
  const reviewFields = document.querySelector("#assistant-review-fields");
  const submitButton = document.querySelector("#assistant-confirm");
  const editButton = document.querySelector("#assistant-edit");
  const errorBox = document.querySelector("#assistant-error");
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
  const data = { name: config.customerName || "", width: "", length: "", height: "" };
  const projectFiles = [];
  const captions = new Map();
  const measurementSources = new Set();
  const greeting = config.customerName
    ? `היי ${config.customerName} 👋 ${config.businessName} הזמין אותך להכין בקשה עבור ״${config.projectLabel}״. מה תרצו לעשות בפרויקט?`
    : "היי, אני OrPro Assist 👋 ספרו לי במילים שלכם: מה תרצו לעשות בבית?";
  const questions = [
    ["project", greeting, "למשל: אני רוצה לשפץ את המטבח..."],
    ["location", "באיזו עיר או אזור נמצא הפרויקט?", "עיר או אזור"],
    ["details", "מה חשוב שבעל העסק ידע? למשל המצב הקיים, הסגנון הרצוי ומתי תרצו להתחיל.", "פרטים נוספים, או 'דלג'"],
    ["photos", "בואו נראה את הפרויקט. אפשר לצלם ארבע זוויות בהדרכה או לצרף תמונות קיימות. אין צורך למדוד.", ""],
    ...(!config.customerName ? [["name", "איך קוראים לכם?", "שם מלא"]] : []),
    ["phone", "מה מספר הטלפון לחזרה?", "050-1234567"],
    ["email", "מה האימייל לקבלת הצעת המחיר? אפשר לכתוב 'דלג'.", "name@example.com"],
  ];
  let step = 0;
  let busy = false;
  let submitted = false;
  const addMessage = (text, type) => {
    const bubble = document.createElement("div");
    bubble.className = `assistant-bubble ${type}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
  };
  const showError = (text) => {
    errorBox.textContent = text;
    errorBox.hidden = !text;
  };
  const ask = () => {
    const [key, question, placeholder] = questions[step];
    addMessage(question, "bot");
    input.placeholder = placeholder;
    input.type = key === "phone" ? "tel" : "text";
    input.inputMode = key === "phone" ? "tel" : key === "email" ? "email" : "text";
    input.maxLength = key === "project" || key === "details" ? 4000 : key === "email" ? 254 : 100;
    upload.hidden = key !== "photos";
    compose.hidden = key === "photos";
    if (key !== "photos") input.focus();
  };
  const categorySlug = (value) => {
    if (config.categorySlug) return config.categorySlug;
    // Routing is confirmed by the customer on the review screen.
    const rules = [
      [/נזיל|צנר|ברז|סתימ|ביוב|אינסטל/, "plumbing"],
      [/פרגול|דק|הצלל/, "pergolas"],
      [/חשמל|שקע|תאור|לוח/, "electricity"],
      [/מטבח|ארון|נגר/, "kitchens"],
      [/שיפו|ריצו|גבס|צבע/, "renovations"],
    ];
    const guess = rules.find(([pattern]) => pattern.test(value))?.[1];
    if (config.categories.some((item) => item.slug === guess)) return guess;
    return config.categories.find((item) => value.includes(item.name))?.slug || "";
  };
  const refreshPhotos = () => {
    photoPreview.replaceChildren();
    photoCount.textContent = projectFiles.length
      ? `צורפו ${projectFiles.length} תמונות. אפשר להוסיף או להסיר לפני השליחה.`
      : "עדיין לא נוספו תמונות פרויקט.";
    projectFiles.forEach((file, index) => {
      const card = document.createElement("figure");
      const image = document.createElement("img");
      const url = URL.createObjectURL(file);
      image.src = url;
      image.alt = captions.get(file) || `תמונה ${index + 1}`;
      image.onload = image.onerror = () => URL.revokeObjectURL(url);
      const caption = document.createElement("figcaption");
      caption.textContent = image.alt;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "הסרה";
      remove.addEventListener("click", () => {
        projectFiles.splice(projectFiles.indexOf(file), 1);
        captions.delete(file);
        refreshPhotos();
      });
      card.append(image, caption, remove);
      photoPreview.appendChild(card);
    });
  };
  const addMeasurementPhoto = (file, caption = "צילום פרויקט") => {
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 10 * 1024 * 1024) {
      showError("אפשר לצרף תמונות JPG, PNG או WEBP עד 10MB לתמונה.");
      return false;
    }
    if (projectFiles.some((item) => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)) return true;
    if (projectFiles.length >= 12) {
      showError("אפשר לצרף עד 12 תמונות. הסירו תמונה לפני הוספת צילום נוסף.");
      return false;
    }
    projectFiles.push(file);
    captions.set(file, caption);
    refreshPhotos();
    return true;
  };
  const finish = () => {
    compose.hidden = true;
    upload.hidden = true;
    review.hidden = false;
    reviewFields.replaceChildren();
    const field = (key, label, value, type = "text") => {
      const wrapper = document.createElement("label");
      wrapper.textContent = label;
      const control = document.createElement(type === "textarea" ? "textarea" : "input");
      if (type !== "textarea") control.type = type;
      control.name = `review_${key}`;
      control.value = value || "";
      control.required = ["name", "phone", "project"].includes(key);
      control.maxLength = key === "project" ? 9000 : key === "phone" ? 30 : key === "email" ? 254 : 100;
      wrapper.appendChild(control);
      reviewFields.appendChild(wrapper);
    };
    field("name", "שם הלקוח", data.name);
    field("phone", "טלפון", data.phone, "tel");
    field("email", "אימייל (לא חובה)", data.email, "email");
    field("location", "עיר / אזור", data.location);
    field("project", "תיאור העבודה", [data.project, data.details].filter(Boolean).join("\n\n"), "textarea");
    if (!config.categorySlug) {
      const label = document.createElement("label");
      label.textContent = "תחום העבודה — ודאו שהבקשה מגיעה לבעל המקצוע הנכון";
      const select = document.createElement("select");
      select.name = "review_category";
      select.required = true;
      select.add(new Option("בחרו תחום", ""));
      config.categories.forEach((item) => select.add(new Option(item.name, item.slug)));
      select.value = categorySlug(data.project);
      label.appendChild(select);
      reviewFields.appendChild(label);
    }
    const summary = document.createElement("p");
    summary.textContent = `${projectFiles.length} תמונות יצורפו לבקשה. יעד: ${config.businessName || "בעלי המקצוע הפעילים בתחום הנבחר"}.`;
    reviewFields.appendChild(summary);
    const measured = ["width", "length", "height"].filter((key) => data[key]);
    if (measured.length) {
      const note = document.createElement("p");
      const labels = { width: "רוחב", length: "אורך", height: "גובה" };
      note.textContent = "מידות משוערות: " + measured.map((key) => `${labels[key]} ${data[key]} מ׳`).join(" · ");
      reviewFields.appendChild(note);
    }
    addMessage("כל הפרטים מוכנים. אפשר לבדוק ולתקן אותם לפני השליחה.", "bot");
  };
  const advance = () => {
    step += 1;
    if (step < questions.length) ask(); else finish();
  };
  const answer = () => {
    if (busy || submitted || step >= questions.length) return;
    const value = input.value.trim();
    if (!value) return;
    const key = questions[step][0];
    if (key === "photos") return;
    if (key === "phone" && (!/^[+\d\s()\-]+$/.test(value) || !/^\d{8,15}$/.test(value.replace(/\D/g, "")))) {
      showError("נא להזין מספר טלפון מלא ותקין.");
      return;
    }
    if (key === "email" && value !== "דלג" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      showError("נא להזין אימייל תקין או לכתוב 'דלג'.");
      return;
    }
    showError("");
    data[key] = value === "דלג" && ["email", "details"].includes(key) ? "" : value;
    addMessage(value, "customer");
    input.value = "";
    advance();
  };
  const submitRequest = async () => {
    if (busy || submitted || !form.reportValidity()) return;
    busy = true;
    submitButton.disabled = true;
    editButton.disabled = true;
    submitButton.textContent = "שומר את הבקשה והתמונות…";
    showError("");
    const payload = new FormData();
    const value = (key) => form.elements.namedItem(`review_${key}`)?.value.trim() || "";
    const fields = {
      name: value("name"), phone: value("phone"), email: value("email"),
      city: value("location"), address: value("location"), description: value("project"),
      service_type: data.project, category: config.categorySlug || value("category"),
      submission_id: config.submissionId,
      estimated_width: data.width || "", estimated_length: data.length || "", estimated_height: data.height || "",
      measurement_method: [...measurementSources].join(", ") || "ללא מדידה",
      csrfmiddlewaretoken: form.elements.namedItem("csrfmiddlewaretoken").value,
    };
    Object.entries(fields).forEach(([key, val]) => payload.append(key, val));
    projectFiles.forEach((file) => {
      payload.append("measurement_photos", file, file.name);
      payload.append("photo_captions", captions.get(file) || "צילום פרויקט");
    });
    try {
      const response = await fetch(config.submitUrl, {
        method: "POST", body: payload, credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const result = await response.json().catch(() => null);
      if (!response.ok || !result?.ok) {
        const details = result?.errors ? Object.values(result.errors).flat().join(" ") : "";
        throw new Error(details || result?.message || "השליחה לא הושלמה. הפרטים והתמונות נשארו כאן; אפשר לנסות שוב.");
      }
      submitted = true;
      review.hidden = true;
      addMessage(`הבקשה נשמרה בהצלחה ✓ מספר בקשה: ${result.requestId}. ${result.direct ? "הפרטים והתמונות זמינים כעת בפאנל של " + result.recipient : "הפרטים והתמונות זמינים כעת לבעלי המקצוע בתחום שנבחר ולמנהל האתר"}.`, "bot");
      stopCamera();
      stopScan();
    } catch (error) {
      showError(error.message || "החיבור הופסק. אפשר לנסות שוב.");
    } finally {
      busy = false;
      submitButton.disabled = false;
      editButton.disabled = false;
      submitButton.textContent = "אישור ושליחת הבקשה";
    }
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!review.hidden) submitRequest(); else answer();
  });
  send.addEventListener("click", answer);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.isComposing) { event.preventDefault(); answer(); }
  });
  photos.addEventListener("change", () => {
    showError("");
    [...photos.files].forEach((file) => addMeasurementPhoto(file));
    photos.value = "";
  });
  const completePhotos = () => {
    if (questions[step]?.[0] !== "photos") return;
    showError("");
    addMessage(projectFiles.length ? `צירפתי ${projectFiles.length} תמונות של הפרויקט` : "אין לי תמונות כרגע", "customer");
    advance();
  };
  photosDone.addEventListener("click", completePhotos);
  skipPhoto.addEventListener("click", completePhotos);
  submitButton.addEventListener("click", submitRequest);
  editButton.addEventListener("click", () => {
    data.name = form.elements.namedItem("review_name").value;
    data.phone = form.elements.namedItem("review_phone").value;
    data.email = form.elements.namedItem("review_email").value;
    data.location = form.elements.namedItem("review_location").value;
    data.project = form.elements.namedItem("review_project").value;
    data.details = "";
    review.hidden = true;
    step = questions.findIndex(([key]) => key === "photos");
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
    arPosition = null;
    arActions.hidden = true;
    arStatus.textContent = "כוונו למשטח ולחצו על שתי נקודות למדידה.";
  };
  const startAR = async () => {
    resetAR();
    if (!navigator.xr) {
      addMessage("מדידת AR אינה נתמכת בדפדפן הזה. אפשר לצלם עם דף A4 ולהזין מידה משוערת.", "bot");
      return;
    }
    try {
      const supported = await navigator.xr.isSessionSupported("immersive-ar");
      if (!supported) throw new Error("unsupported");
      arScreen.hidden = false;
      const gl = arCanvas.getContext("webgl", { xrCompatible: true });
      arSession = await navigator.xr.requestSession("immersive-ar", { requiredFeatures: ["hit-test", "local-floor", "dom-overlay"], domOverlay: { root: arScreen } });
      await gl.makeXRCompatible();
      arSession.updateRenderState({ baseLayer: new XRWebGLLayer(arSession, gl) });
      const referenceSpace = await arSession.requestReferenceSpace("local-floor");
      const viewerSpace = await arSession.requestReferenceSpace("viewer");
      const hitTestSource = await arSession.requestHitTestSource({ space: viewerSpace });
      arSession.addEventListener("end", () => { arScreen.hidden = true; arSession = null; });
      arSession.addEventListener("select", () => {
        if (!arPosition || arPoints.length === 2) return;
        arPoints.push({ x: arPosition.x, y: arPosition.y, z: arPosition.z });
        if (arPoints.length === 1) arStatus.textContent = "נקודה ראשונה נשמרה. לחצו על נקודת הסיום.";
        if (arPoints.length === 2) {
          const meters = distance(arPoints[0], arPoints[1]).toFixed(2);
          arStatus.textContent = `נמדדו ${meters} מטרים. לאיזו מידה לשמור?`;
          arActions.hidden = false;
        }
      });
      const frameLoop = (_, frame) => {
        if (!arSession) return;
        arSession.requestAnimationFrame(frameLoop);
        const baseLayer = arSession.renderState.baseLayer;
        gl.bindFramebuffer(gl.FRAMEBUFFER, baseLayer.framebuffer);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        const hits = frame.getHitTestResults(hitTestSource);
        arPosition = null;
        if (hits.length) {
          const pose = hits[0].getPose(referenceSpace);
          arPosition = pose?.transform.position || null;
        }
        if (arPoints.length < 2) arStatus.textContent = arPosition ? (arPoints.length ? "כוונו את מרכז המסך לסיום והקישו." : "כוונו את מרכז המסך להתחלה והקישו.") : "מחפש משטח. הזיזו את המצלמה באיטיות.";
      };
      arSession.requestAnimationFrame(frameLoop);
    } catch (_) {
      if (arSession) await stopAR();
      arScreen.hidden = true;
      addMessage("לא ניתן לפתוח AR במכשיר הזה. נסו Chrome במכשיר Android או השתמשו בצילום עם דף A4.", "bot");
    }
  };
  arStart.addEventListener("click", startAR);
  arClose.addEventListener("click", stopAR);
  arReset.addEventListener("click", resetAR);
  document.querySelectorAll("[data-ar-dimension]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (arPoints.length !== 2) return;
      const meters = distance(arPoints[0], arPoints[1]).toFixed(2);
      if (!Number.isFinite(Number(meters)) || Number(meters) <= 0 || Number(meters) > 9999.99) return;
      measurementSources.add("AR");
      data[button.dataset.arDimension] = meters;
      addMessage(`מדידת AR נשמרה: ${button.dataset.arDimension === "width" ? "רוחב" : "אורך"} ${meters} מ׳`, "customer");
      await stopAR();
    });
  });
  [arClose, arReset, arActions].forEach((control) => control.addEventListener("beforexrselect", (event) => event.preventDefault()));

  let a4Points = [];
  let measurePoints = [];
  let a4Homography;
  let a4Image;
  let cameraStream;
  let scanStream;
  let scanIndex = 0;
  const stopCamera = () => {
    if (cameraStream) cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
    a4Video.srcObject = null;
  };
  const stopScan = () => {
    if (scanStream) scanStream.getTracks().forEach((track) => track.stop());
    scanStream = null;
    scanVideo.srcObject = null;
    scanScreen.hidden = true;
  };
  const loadA4Image = (source, file) => {
    if (file && !addMeasurementPhoto(file, "צילום כיול A4")) { URL.revokeObjectURL(source); return; }
    a4Image = new Image();
    a4Image.onload = () => { resetA4(); a4Camera.hidden = true; URL.revokeObjectURL(source); };
    a4Image.onerror = () => { URL.revokeObjectURL(source); showError("לא הצלחנו לקרוא את התמונה. נסו צילום אחר."); };
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
    stopCamera();
    a4Screen.hidden = false;
    a4Camera.hidden = false;
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      if (a4Screen.hidden) { stopCamera(); return; }
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
    if (!a4Video.videoWidth || a4Capture.disabled) return;
    a4Capture.disabled = true;
    const snapshot = document.createElement("canvas");
    snapshot.width = a4Video.videoWidth; snapshot.height = a4Video.videoHeight;
    snapshot.getContext("2d").drawImage(a4Video, 0, 0);
    snapshot.toBlob((blob) => {
      a4Capture.disabled = false;
      if (!blob || a4Screen.hidden) return;
      const file = new File([blob], `measurement-${Date.now()}.jpg`, { type: "image/jpeg" });
      stopCamera();
      loadA4Image(URL.createObjectURL(file), file);
    }, "image/jpeg", 0.92);
  });
  const scanSteps = ["תמונה כללית של כל השטח", "צילום מצד ימין של אזור העבודה", "צילום מהצד הנגדי כדי להבין עומק", "צילום מקרוב של הפרט החשוב או התקלה"];
  scanStart.addEventListener("click", async () => {
    stopScan();
    scanIndex = 0;
    scanScreen.hidden = false;
    scanCapture.disabled = false;
    scanStatus.textContent = "נצלם ארבע זוויות של הפרויקט.";
    scanPrompt.textContent = `צילום 1 מתוך 4: ${scanSteps[0]}`;
    try {
      scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
      if (scanScreen.hidden) { stopScan(); return; }
      scanVideo.srcObject = scanStream;
    } catch (_) {
      stopScan();
      addMessage("לא ניתן לפתוח מצלמה לסריקה. אפשר לצרף תמונות רגילות מהטלפון.", "bot");
    }
  });
  scanClose.addEventListener("click", stopScan);
  scanCapture.addEventListener("click", () => {
    if (!scanVideo.videoWidth || scanCapture.disabled) return;
    scanCapture.disabled = true;
    const capturedIndex = scanIndex;
    const snapshot = document.createElement("canvas");
    snapshot.width = scanVideo.videoWidth; snapshot.height = scanVideo.videoHeight;
    snapshot.getContext("2d").drawImage(scanVideo, 0, 0);
    snapshot.toBlob((blob) => {
      scanCapture.disabled = false;
      if (!blob || scanScreen.hidden || capturedIndex !== scanIndex) return;
      if (!addMeasurementPhoto(new File([blob], `project-scan-${Date.now()}-${scanIndex + 1}.jpg`, { type: "image/jpeg" }), scanSteps[scanIndex])) { stopScan(); return; }
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
      if (!Number.isFinite(Number(meters)) || Number(meters) <= 0 || Number(meters) > 9999.99) return;
      measurementSources.add("צילום A4");
      data[button.dataset.a4Dimension] = meters;
      addMessage(`מדידה מצילום A4 נשמרה: ${button.dataset.a4Dimension === "width" ? "רוחב" : "אורך"} ${meters} מ׳`, "customer");
      a4Screen.hidden = true;
      if (questions[step]?.[0] === "photos") addMessage("צירפתי גם צילום מדידה עם דף A4", "customer");
    });
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden) { stopCamera(); stopScan(); } });
  window.addEventListener("pagehide", () => { stopCamera(); stopScan(); });
  ask();
})();
