import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';
import SocialLoginButtons from '../components/SocialLoginButtons';
import './LoginPage.css';

const KYU_SCHOOLS = [
  'School of Business & Education',
  'School of Pure & Applied Sciences',
  'School of Health Sciences',
  'School of Engineering & Technology',
  'School of Hospitality & Textile Technology',
];

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    username: '',
    department: '',
    student_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const { register } = useAuth();
  const navigate = useNavigate();

  const validateEmail = (email) => /^[a-zA-Z0-9._%+-]+@(students\.kyu\.ac\.ke|staffs\.kyu\.ac\.ke|kyu\.ac\.ke)$/.test(email);

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const validateStep1 = () => {
    if (!formData.full_name.trim()) { toast.error('Full name is required'); return false; }
    if (!validateEmail(formData.email)) { toast.error('Use a valid @students.kyu.ac.ke or @staffs.kyu.ac.ke email'); return false; }
    if (formData.password.length < 6) { toast.error('Password must be at least 6 characters'); return false; }
    if (formData.password !== formData.confirmPassword) { toast.error('Passwords do not match'); return false; }
    return true;
  };

  const handleNextStep = () => {
    if (validateStep1()) setStep(2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.username.trim()) { toast.error('Registration number is required'); return; }
    if (!formData.department) { toast.error('Select a school'); return; }
    setLoading(true);
    try {
      await register({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        username: formData.username,
        department: formData.department,
        student_id: formData.student_id || formData.username,
      });
      toast.success('Account created! Welcome to Campus Connect');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ku-login-page">
      <div className="ku-login-bg" />
      <div className="ku-login-container" style={{ maxWidth: 480 }}>
        <div className="ku-login-header">
          <img src="/images/kyu-logo.png" alt="KyU Logo" className="ku-login-logo" />
          <h1>KyU Campus Connect</h1>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 12 }}>
            <span style={{
              padding: '4px 14px', borderRadius: 12, fontSize: 12, fontWeight: 600,
              background: step >= 1 ? '#c8a84e' : 'rgba(255,255,255,0.2)', color: step >= 1 ? '#1a1a1a' : '#fff'
            }}>1. Account</span>
            <span style={{ color: 'rgba(255,255,255,0.4)' }}>→</span>
            <span style={{
              padding: '4px 14px', borderRadius: 12, fontSize: 12, fontWeight: 600,
              background: step >= 2 ? '#c8a84e' : 'rgba(255,255,255,0.2)', color: step >= 2 ? '#1a1a1a' : '#fff'
            }}>2. Academic</span>
          </div>
        </div>
        <div className="ku-login-body">
          {step === 1 && (
            <div className="ku-login-form">
              <div className="ku-form-group">
                <label>Full Name</label>
                <input name="full_name" placeholder="e.g John Mwangi Kamau" value={formData.full_name} onChange={handleChange} />
              </div>
              <div className="ku-form-group">
                <label>University Email</label>
                <input name="email" type="email" placeholder="your.name@students.kyu.ac.ke" value={formData.email} onChange={handleChange}
                  style={formData.email && !validateEmail(formData.email) ? { borderColor: '#e74c3c' } : {}} />
                {formData.email && !validateEmail(formData.email) && (
                  <span style={{ color: '#e74c3c', fontSize: 12 }}>Must be a valid @students.kyu.ac.ke or @staffs.kyu.ac.ke email</span>
                )}
              </div>
              <div className="ku-form-group">
                <label>Password</label>
                <input name="password" type="password" placeholder="Min 6 characters" value={formData.password} onChange={handleChange} />
              </div>
              <div className="ku-form-group">
                <label>Confirm Password</label>
                <input name="confirmPassword" type="password" placeholder="Confirm password" value={formData.confirmPassword} onChange={handleChange} />
              </div>
              <button type="button" className="ku-btn-signin" onClick={handleNextStep} style={{ width: '100%' }}>Next →</button>
              <div className="ku-social-section">
                <div className="ku-social-divider"><span>or sign up with</span></div>
                <SocialLoginButtons mode="register" />
              </div>
            </div>
          )}
          {step === 2 && (
            <form onSubmit={handleSubmit} className="ku-login-form">
              <div className="ku-form-group">
                <label>Registration Number</label>
                <input name="username" placeholder="e.g CT101/G/25159/24" value={formData.username} onChange={handleChange} />
                <span style={{ color: '#888', fontSize: 11 }}>Format: Department/Level/Number/Year</span>
              </div>
              <div className="ku-form-group">
                <label>School</label>
                <select name="department" value={formData.department} onChange={handleChange}
                  style={{ padding: '12px 14px', border: '2px solid #e0d8c8', borderRadius: 6, fontSize: 15, background: '#fefcf6' }}>
                  <option value="">Select school</option>
                  {KYU_SCHOOLS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="ku-form-group">
                <label>Student ID / National ID (optional)</label>
                <input name="student_id" placeholder="e.g 34567890" value={formData.student_id} onChange={handleChange} />
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <button type="button" className="ku-btn-forgot" onClick={() => setStep(1)} style={{ flex: 1 }}>← Back</button>
                <button type="submit" className="ku-btn-signin" disabled={loading} style={{ flex: 2 }}>
                  {loading ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          )}
          <div className="ku-login-footer">
            <p>Already have an account? <Link to="/login">Sign In</Link></p>
          </div>
        </div>
      </div>
      <div className="ku-login-info">
        <p>Innovative Technology for a Dynamic World</p>
        <p className="ku-iso">Kirinyaga University is ISO 9001:2015 Certified</p>
      </div>
    </div>
  );
}
