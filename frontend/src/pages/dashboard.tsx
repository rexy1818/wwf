import Sidebar from "../components/Sidebar";

export default function Dashboard() {
  return (
    <>
      <Sidebar />

      <main
        style={{
          marginLeft: "260px",
          padding: "40px",
        }}
      >
        <h1>Dashboard Principal</h1>

        <p>
          Bienvenido al sistema de monitoreo WWF.
        </p>
      </main>
    </>
  );
}