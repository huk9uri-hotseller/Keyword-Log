import "../App.css";

export default function LoginCard() {
  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-title">
          <h1>Keyword Log</h1>
          <p>사용자 로그인</p>
        </div>
        <form className="login-form">
          <label>
            이메일
            <input type="email" placeholder="이메일을 입력해주세요" />
          </label>
          <label>
            비밀번호
            <input type="password" placeholder="비밀번호를 입력해주세요" />
          </label>
          <button type="submit" className="primary-button">
            로그인
          </button>
          <button type="button" className="secondary-button">
            회원가입
          </button>
        </form>
      </div>
    </div>
  );
}
