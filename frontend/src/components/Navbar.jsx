function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-title">
        Dashboard Overview
      </div>

      <div className="navbar-right">

        <div className="user-section">
          <div className="user-avatar">SH</div>

          <div className="user-info">
            <p className="user-name">Shivanshu Sharma</p>
            <p className="user-role">Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Navbar;