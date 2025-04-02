import React, { useState, useEffect } from 'react';

function App() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/users')
      .then(response => response.json())
      .then(data => {
        setUsers(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching users:', error);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ textAlign: 'center', backgroundColor: '#282c34', color: 'white', padding: '20px', borderRadius: '5px' }}>
        Microservices Frontend
      </h1>
      
      <div style={{ marginTop: '20px' }}>
        <h2>User List</h2>
        
        {loading ? (
          <p>Loading users...</p>
        ) : (
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            {users.length === 0 ? (
              <p>No users found. Try adding some!</p>
            ) : (
              users.map(user => (
                <li key={user.id} style={{ padding: '10px', borderBottom: '1px solid #eee' }}>
                  <strong>{user.name}</strong> ({user.email})
                </li>
              ))
            )}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App;