import cv2
vid = cv2.VideoCapture("./akha.mp4")
    if not vid.isOpened():
        print("Error: Video file not found or cannot be opened.")
        return

    fps = vid.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps)

    cv2.namedWindow('Idle Video', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Idle Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while global_state.run_idle_video:
        ret, frame = vid.read()

        if not ret:
            vid.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
            continue

        cv2.imshow('Idle Video', frame)

        if cv2.waitKey(delay) & 0xFF == ord('d'):
            break

    vid.release()
    cv2.destroyAllWindows()