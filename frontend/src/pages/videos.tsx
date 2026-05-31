import Sidebar from "../components/Sidebar";
import { VideoModule } from "./Video";
import "../styles/video.css";

export default function Videos() {
  return (
    <>
      <Sidebar />

      <main className="videos-container legacy-video-page">
        <VideoModule />
      </main>
    </>
  );
}
