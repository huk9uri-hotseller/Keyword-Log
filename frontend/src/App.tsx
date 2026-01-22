import { useEffect, useMemo, useState } from "react";
import "./App.css";
import type { Keyword, KeywordGroup, KeywordType, User } from "./types";
import { createUser, fetchUsers } from "./api/users";
import {
  createKeywordGroup,
  deleteKeywordGroup,
  fetchKeywordGroups,
  updateKeywordGroup,
} from "./api/keywordGroups";
import {
  createKeyword,
  deleteKeyword,
  fetchKeywords,
  updateKeyword,
} from "./api/keywords";

type LoadState = "idle" | "loading" | "success" | "error";

const keywordTypeOptions: KeywordType[] = ["GENERAL", "OWN", "COMPETITOR"];

export default function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [userState, setUserState] = useState<LoadState>("idle");
  const [userError, setUserError] = useState<string>("");

  const [groups, setGroups] = useState<KeywordGroup[]>([]);
  const [groupState, setGroupState] = useState<LoadState>("idle");
  const [groupError, setGroupError] = useState<string>("");

  const [keywords, setKeywords] = useState<Record<number, Keyword[]>>({});
  const [keywordState, setKeywordState] = useState<Record<number, LoadState>>(
    {}
  );
  const [keywordError, setKeywordError] = useState<Record<number, string>>({});

  const [selectedUserId, setSelectedUserId] = useState<string>("");

  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [newUserPicture, setNewUserPicture] = useState("");
  const [newUserSub, setNewUserSub] = useState("");

  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupType, setNewGroupType] = useState<KeywordType>("GENERAL");
  const [newGroupUserId, setNewGroupUserId] = useState("");

  const [newKeywordByGroup, setNewKeywordByGroup] = useState<
    Record<number, string>
  >({});

  const [editGroupName, setEditGroupName] = useState<Record<number, string>>(
    {}
  );

  const resolvedUserId = useMemo(() => {
    if (!selectedUserId) {
      return undefined;
    }
    const parsed = Number(selectedUserId);
    return Number.isNaN(parsed) ? undefined : parsed;
  }, [selectedUserId]);

  const loadUsers = async () => {
    setUserState("loading");
    setUserError("");
    try {
      const data = await fetchUsers();
      setUsers(data);
      setUserState("success");
    } catch (error) {
      setUserState("error");
      setUserError(error instanceof Error ? error.message : "요청 실패");
    }
  };

  const loadGroups = async (userId?: number) => {
    setGroupState("loading");
    setGroupError("");
    try {
      const data = await fetchKeywordGroups(userId);
      setGroups(data);
      setGroupState("success");
    } catch (error) {
      setGroupState("error");
      setGroupError(error instanceof Error ? error.message : "요청 실패");
    }
  };

  const loadKeywords = async (groupId: number) => {
    setKeywordState((prev) => ({ ...prev, [groupId]: "loading" }));
    setKeywordError((prev) => ({ ...prev, [groupId]: "" }));
    try {
      const data = await fetchKeywords(groupId);
      setKeywords((prev) => ({ ...prev, [groupId]: data }));
      setKeywordState((prev) => ({ ...prev, [groupId]: "success" }));
    } catch (error) {
      setKeywordState((prev) => ({ ...prev, [groupId]: "error" }));
      setKeywordError((prev) => ({
        ...prev,
        [groupId]: error instanceof Error ? error.message : "요청 실패",
      }));
    }
  };

  useEffect(() => {
    loadUsers();
    loadGroups();
  }, []);

  const handleCreateUser = async () => {
    setUserError("");
    try {
      await createUser({
        email: newUserEmail.trim(),
        name: newUserName.trim() || undefined,
        picture_url: newUserPicture.trim() || undefined,
        google_sub: newUserSub.trim(),
      });
      setNewUserEmail("");
      setNewUserName("");
      setNewUserPicture("");
      setNewUserSub("");
      await loadUsers();
    } catch (error) {
      setUserError(error instanceof Error ? error.message : "요청 실패");
    }
  };

  const handleCreateGroup = async () => {
    setGroupError("");
    const userIdValue = Number(newGroupUserId);
    if (!newGroupName.trim() || Number.isNaN(userIdValue)) {
      setGroupError("사용자 ID와 그룹 이름을 확인해주세요.");
      return;
    }
    try {
      await createKeywordGroup({
        user_id: userIdValue,
        group_name: newGroupName.trim(),
        keyword_type: newGroupType,
      });
      setNewGroupName("");
      setNewGroupUserId("");
      await loadGroups(resolvedUserId);
    } catch (error) {
      setGroupError(error instanceof Error ? error.message : "요청 실패");
    }
  };

  const handleUpdateGroupName = async (groupId: number) => {
    const name = editGroupName[groupId]?.trim();
    if (!name) {
      setGroupError("그룹 이름을 입력해주세요.");
      return;
    }
    setGroupError("");
    try {
      await updateKeywordGroup(groupId, { group_name: name });
      await loadGroups(resolvedUserId);
    } catch (error) {
      setGroupError(error instanceof Error ? error.message : "요청 실패");
    }
  };

  const handleDeleteGroup = async (groupId: number) => {
    setGroupError("");
    try {
      await deleteKeywordGroup(groupId);
      setKeywords((prev) => {
        const next = { ...prev };
        delete next[groupId];
        return next;
      });
      await loadGroups(resolvedUserId);
    } catch (error) {
      setGroupError(error instanceof Error ? error.message : "요청 실패");
    }
  };

  const handleCreateKeyword = async (groupId: number) => {
    const keyword = newKeywordByGroup[groupId]?.trim();
    if (!keyword) {
      setKeywordError((prev) => ({
        ...prev,
        [groupId]: "키워드를 입력해주세요.",
      }));
      return;
    }
    setKeywordError((prev) => ({ ...prev, [groupId]: "" }));
    try {
      await createKeyword(groupId, { keyword, is_active: true });
      setNewKeywordByGroup((prev) => ({ ...prev, [groupId]: "" }));
      await loadKeywords(groupId);
    } catch (error) {
      setKeywordError((prev) => ({
        ...prev,
        [groupId]: error instanceof Error ? error.message : "요청 실패",
      }));
    }
  };

  const handleToggleKeyword = async (groupId: number, item: Keyword) => {
    setKeywordError((prev) => ({ ...prev, [groupId]: "" }));
    try {
      await updateKeyword(groupId, item.id, {
        is_active: !item.is_active,
      });
      await loadKeywords(groupId);
    } catch (error) {
      setKeywordError((prev) => ({
        ...prev,
        [groupId]: error instanceof Error ? error.message : "요청 실패",
      }));
    }
  };

  const handleRenameKeyword = async (
    groupId: number,
    keywordId: number,
    newValue: string
  ) => {
    const value = newValue.trim();
    if (!value) {
      setKeywordError((prev) => ({
        ...prev,
        [groupId]: "키워드를 입력해주세요.",
      }));
      return;
    }
    setKeywordError((prev) => ({ ...prev, [groupId]: "" }));
    try {
      await updateKeyword(groupId, keywordId, { keyword: value });
      await loadKeywords(groupId);
    } catch (error) {
      setKeywordError((prev) => ({
        ...prev,
        [groupId]: error instanceof Error ? error.message : "요청 실패",
      }));
    }
  };

  const handleDeleteKeyword = async (groupId: number, keywordId: number) => {
    setKeywordError((prev) => ({ ...prev, [groupId]: "" }));
    try {
      await deleteKeyword(groupId, keywordId);
      await loadKeywords(groupId);
    } catch (error) {
      setKeywordError((prev) => ({
        ...prev,
        [groupId]: error instanceof Error ? error.message : "요청 실패",
      }));
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>K-LOG 키워드 관리자</h1>
          <p>백엔드 CRUD 연동용 간단 UI</p>
        </div>
      </header>

      <section className="panel">
        <h2>사용자</h2>
        <div className="grid">
          <div>
            <h3>사용자 생성</h3>
            <div className="form">
              <label>
                이메일
                <input
                  value={newUserEmail}
                  onChange={(event) => setNewUserEmail(event.target.value)}
                  placeholder="example@domain.com"
                />
              </label>
              <label>
                이름
                <input
                  value={newUserName}
                  onChange={(event) => setNewUserName(event.target.value)}
                  placeholder="홍길동"
                />
              </label>
              <label>
                프로필 이미지 URL
                <input
                  value={newUserPicture}
                  onChange={(event) => setNewUserPicture(event.target.value)}
                  placeholder="https://..."
                />
              </label>
              <label>
                Google Sub
                <input
                  value={newUserSub}
                  onChange={(event) => setNewUserSub(event.target.value)}
                  placeholder="google-sub"
                />
              </label>
              <button
                type="button"
                onClick={handleCreateUser}
                disabled={!newUserEmail || !newUserSub}
              >
                사용자 생성
              </button>
              {userError && <p className="error">{userError}</p>}
            </div>
          </div>
          <div>
            <h3>사용자 목록</h3>
            <button type="button" onClick={loadUsers} className="ghost">
              새로고침
            </button>
            {userState === "loading" && <p>불러오는 중...</p>}
            <ul className="list">
              {users.map((user) => (
                <li key={user.id}>
                  <strong>{user.email}</strong>
                  <span className="muted">
                    ID {user.id}
                    {user.name ? ` · ${user.name}` : ""}
                  </span>
                </li>
              ))}
            </ul>
            {!users.length && userState !== "loading" && (
              <p className="muted">등록된 사용자가 없습니다.</p>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>키워드 그룹</h2>
          <div className="inline">
            <label>
              사용자 ID로 필터
              <input
                value={selectedUserId}
                onChange={(event) => setSelectedUserId(event.target.value)}
                placeholder="예: 1"
              />
            </label>
            <button
              type="button"
              onClick={() => loadGroups(resolvedUserId)}
              className="ghost"
            >
              조회
            </button>
          </div>
        </div>
        <div className="grid">
          <div>
            <h3>그룹 생성</h3>
            <div className="form">
              <label>
                사용자 ID
                <input
                  value={newGroupUserId}
                  onChange={(event) => setNewGroupUserId(event.target.value)}
                  placeholder="예: 1"
                />
              </label>
              <label>
                그룹 이름
                <input
                  value={newGroupName}
                  onChange={(event) => setNewGroupName(event.target.value)}
                  placeholder="브랜드 키워드"
                />
              </label>
              <label>
                그룹 타입
                <select
                  value={newGroupType}
                  onChange={(event) =>
                    setNewGroupType(event.target.value as KeywordType)
                  }
                >
                  {keywordTypeOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <button type="button" onClick={handleCreateGroup}>
                그룹 생성
              </button>
              {groupError && <p className="error">{groupError}</p>}
            </div>
          </div>
          <div>
            <h3>그룹 목록</h3>
            <button
              type="button"
              onClick={() => loadGroups(resolvedUserId)}
              className="ghost"
            >
              새로고침
            </button>
            {groupState === "loading" && <p>불러오는 중...</p>}
            <div className="group-list">
              {groups.map((group) => (
                <div key={group.id} className="group-card">
                  <div className="group-title">
                    <div>
                      <strong>{group.group_name}</strong>
                      <span className="muted">
                        ID {group.id} · 사용자 {group.user_id} ·{" "}
                        {group.keyword_type}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteGroup(group.id)}
                      className="danger"
                    >
                      삭제
                    </button>
                  </div>
                  <div className="inline">
                    <input
                      value={editGroupName[group.id] ?? ""}
                      onChange={(event) =>
                        setEditGroupName((prev) => ({
                          ...prev,
                          [group.id]: event.target.value,
                        }))
                      }
                      placeholder="새 그룹 이름"
                    />
                    <button
                      type="button"
                      onClick={() => handleUpdateGroupName(group.id)}
                    >
                      이름 변경
                    </button>
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => loadKeywords(group.id)}
                    >
                      키워드 조회
                    </button>
                  </div>

                  <div className="keyword-panel">
                    <h4>키워드</h4>
                    <div className="inline">
                      <input
                        value={newKeywordByGroup[group.id] ?? ""}
                        onChange={(event) =>
                          setNewKeywordByGroup((prev) => ({
                            ...prev,
                            [group.id]: event.target.value,
                          }))
                        }
                        placeholder="키워드 입력"
                      />
                      <button
                        type="button"
                        onClick={() => handleCreateKeyword(group.id)}
                      >
                        추가
                      </button>
                    </div>
                    {keywordError[group.id] && (
                      <p className="error">{keywordError[group.id]}</p>
                    )}
                    {keywordState[group.id] === "loading" && (
                      <p>불러오는 중...</p>
                    )}
                    <ul className="list">
                      {(keywords[group.id] ?? []).map((item) => (
                        <li key={item.id} className="keyword-row">
                          <span className={item.is_active ? "" : "muted"}>
                            {item.keyword}
                          </span>
                          <div className="inline">
                            <button
                              type="button"
                              className="ghost"
                              onClick={() => handleToggleKeyword(group.id, item)}
                            >
                              {item.is_active ? "비활성" : "활성"}
                            </button>
                            <button
                              type="button"
                              className="ghost"
                              onClick={() =>
                                handleRenameKeyword(
                                  group.id,
                                  item.id,
                                  prompt(
                                    "새 키워드를 입력해주세요.",
                                    item.keyword
                                  ) ?? ""
                                )
                              }
                            >
                              이름 변경
                            </button>
                            <button
                              type="button"
                              className="danger"
                              onClick={() => handleDeleteKeyword(group.id, item.id)}
                            >
                              삭제
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                    {!keywords[group.id]?.length &&
                      keywordState[group.id] === "success" && (
                        <p className="muted">등록된 키워드가 없습니다.</p>
                      )}
                  </div>
                </div>
              ))}
              {!groups.length && groupState !== "loading" && (
                <p className="muted">등록된 그룹이 없습니다.</p>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
