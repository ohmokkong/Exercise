#!/usr/bin/env python3
import sqlite3
import argparse
import sys
from typing import Optional, List, Tuple, Any # 타입 힌트 추가

DB_NAME = 'greetings.db'


class DatabaseManager:
    """데이터베이스 연결을 관리하는 컨텍스트 관리자 클래스"""

    def __init__(self, db_name: str):
        self.db_name: str = db_name
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        """컨텍스트 관리자 진입 시 데이터베이스 연결"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            return self.conn
        except sqlite3.Error as e:
            print(f"데이터베이스 연결 오류: {e}")
            sys.exit(1)

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]):
        """컨텍스트 관리자 종료 시 데이터베이스 연결 종료 및 커밋/롤백"""
        if self.conn:
            if exc_type is None:  # 오류가 없을 경우 커밋
                try:
                    self.conn.commit()
                except sqlite3.Error as e:
                    print(f"커밋 오류: {e}") # 커밋 중 오류 발생 가능성 처리
            else: # 오류 발생 시 롤백 (선택적)
                self.conn.rollback() # 필요 시 롤백 로직 추가
                print(f"오류 발생 ({exc_val}). 변경 사항이 롤백되었습니다.") # 롤백 메시지 수정
            self.conn.close()
        # 오류를 다시 발생시키도록 False (기본값) 유지
        return False


def initialize_db(db_manager: DatabaseManager):
    """데이터베이스와 테이블을 초기화합니다 (테이블이 없을 경우 생성)."""
    try:
        with db_manager as conn: # with 문 사용
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            ''')
            # conn.commit() # __exit__에서 처리
    except sqlite3.Error as e:
        print(f"데이터베이스 초기화 오류: {e}")
    # finally: db_manager.close() # __exit__에서 처리


def reset_db(db_manager: DatabaseManager):
    """데이터베이스를 초기화합니다 (모든 데이터 삭제 및 테이블 재생성)."""
    # 사용자 확인은 데이터베이스 연결 전에 수행
    confirmation = input("정말로 데이터베이스를 초기화하시겠습니까? (y/n): ")
    if confirmation.lower() != 'y':
        print("데이터베이스 초기화가 취소되었습니다.")
        return

    try:
        with db_manager as conn: # with 문 사용
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS names")
            cursor.execute('''
            CREATE TABLE names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            ''')
            # conn.commit() # __exit__에서 처리
            print("데이터베이스가 초기화되었습니다.")
    except sqlite3.Error as e:
        print(f"데이터베이스 초기화 오류: {e}")
    # finally: db_manager.close() # __exit__에서 처리


def add_name(db_manager: DatabaseManager, name: str) -> bool:
    """데이터베이스에 이름을 추가합니다. UNIQUE 제약 조건을 활용합니다."""
    try:
        with db_manager as conn: # with 문 사용
            cursor = conn.cursor()
            # SELECT 쿼리 제거 - UNIQUE 제약 조건에 의존
            cursor.execute("INSERT INTO names (name) VALUES (?)", (name,))
            # conn.commit() # __exit__에서 처리
            print(f"'{name}'님, 데이터베이스에 저장되었습니다.")
            return True
    except sqlite3.IntegrityError: # UNIQUE 제약 조건 위반 시 발생
        print(f"'{name}'님은 이미 데이터베이스에 존재합니다.")
        return False
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
        return False
    # finally: db_manager.close() # __exit__에서 처리


def update_name(db_manager: DatabaseManager, old_name: str, new_name: str):
    """데이터베이스의 이름을 변경합니다."""
    if old_name == new_name:
        print("변경 전 이름과 변경 후 이름이 동일합니다.")
        return

    try:
        with db_manager as conn: # with 문 사용
            cursor = conn.cursor()
            # 변경 전 이름 존재 확인
            cursor.execute("SELECT id FROM names WHERE name = ?", (old_name,))
            result = cursor.fetchone()
            if result:
                # 이름 변경 실행
                cursor.execute("UPDATE names SET name = ? WHERE name = ?", (new_name, old_name))
                # conn.commit() # __exit__에서 처리
                if cursor.rowcount > 0:
                    print(f"'{old_name}'을(를) '{new_name}'(으)로 성공적으로 변경했습니다.")
                else:
                    # rowcount가 0인 경우는 드물게 다른 연결에서 해당 행이 삭제된 경우일 수 있습니다.
                    print(f"'{old_name}'을(를) 찾았지만 변경되지 않았습니다. (다른 문제 발생)")
            else:
                print(f"'{old_name}'을(를) 찾을 수 없습니다.")
    except sqlite3.IntegrityError: # 새 이름이 이미 존재할 경우
        print(f"'{new_name}'은(는) 이미 데이터베이스에 존재합니다.")
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
    # finally: db_manager.close() # __exit__에서 처리


def delete_name(db_manager: DatabaseManager, name: str):
    """데이터베이스에서 이름을 삭제합니다."""
    try:
        with db_manager as conn: # with 문 사용
            cursor = conn.cursor()
            cursor.execute("DELETE FROM names WHERE name = ?", (name,))
            # conn.commit() # __exit__에서 처리
            if cursor.rowcount > 0:
                print(f"'{name}'을(를) 성공적으로 삭제했습니다.")
            else:
                print(f"'{name}'을(를) 찾을 수 없습니다.")
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
    # finally: db_manager.close() # __exit__에서 처리


def print_all_names(db_manager: DatabaseManager):
    """데이터베이스의 모든 이름을 출력합니다."""
    try:
        # 읽기 전용 작업이지만 일관성을 위해 with 사용
        with db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM names ORDER BY name")
            all_names: List[Tuple[str]] = cursor.fetchall()
            print("\n--- 저장된 이름 목록 ---")
            if not all_names:
                print("저장된 이름이 없습니다.")
            else:
                for idx, row in enumerate(all_names):
                    print(f"{idx + 1}. {row[0]}")
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
    # finally: db_manager.close() # __exit__에서 처리


def main():
    """메인 실행 함수"""
    db_manager = DatabaseManager(DB_NAME)

    parser = argparse.ArgumentParser(
        description="이름을 관리하는 프로그램",
        epilog="예시: python name.py -i Alice / python name.py -u Alice Bob / python name.py -o"
    )

    # 작업 선택을 위한 뮤추얼리 익스클루시브 그룹
    action_group = parser.add_mutually_exclusive_group(required=False) # 어떤 옵션도 주어지지 않으면 도움말 출력하도록 required=False 유지
    action_group.add_argument('-i', '--input', type=str, metavar='NAME', help="데이터베이스에 추가할 이름을 지정합니다.")
    # --update 인수 처리 방식 변경: nargs=2 사용
    action_group.add_argument('-u', '--update', type=str, nargs=2, metavar=('OLD_NAME', 'NEW_NAME'),
                              help="데이터베이스의 이름을 변경합니다. 예: -u old_name new_name")
    action_group.add_argument('-d', '--delete', type=str, metavar='NAME', help="데이터베이스에서 삭제할 이름을 지정합니다.")
    action_group.add_argument('-o', '--output', action='store_true', help="출력 모드를 활성화합니다. 모든 이름을 출력합니다.")
    # --initialize 옵션은 별도로 처리 (그룹에 포함시키지 않음)
    parser.add_argument('-init', '--initialize', action='store_true', help="데이터베이스를 초기화합니다 (모든 데이터 삭제).")
    # 테스트용 오류 발생 옵션 추가
    parser.add_argument('--test-error', action='store_true', help="롤백 테스트를 위해 의도적으로 오류를 발생시킵니다.")

    args = parser.parse_args()

    # 어떤 작업도 명시되지 않았는지 확인 (initialize 제외)
    action_specified = args.input or args.update or args.delete or args.output

    if args.initialize:
        reset_db(db_manager)
        # 초기화 후에는 다른 작업을 수행하지 않고 종료
        sys.exit(0)

    # initialize가 아니고 다른 작업도 명시되지 않았으면 도움말 출력
    if not action_specified:
         parser.print_help()
         sys.exit(0) # 도움말 출력 후 정상 종료

    # initialize가 아니고 다른 작업이 명시된 경우 DB 초기화 (테이블 생성)
    # 단, 테스트 오류 발생 시에는 DB 초기화 불필요
    if not args.test_error:
        initialize_db(db_manager)

    # 테스트 오류 발생 처리
    if args.test_error:
        print("--- 오류 발생 테스트 시작 ---")
        try:
            with db_manager as conn:
                cursor = conn.cursor()
                # 간단한 작업 시도
                cursor.execute("INSERT INTO names (name) VALUES (?)", ("TestErrorName",))
                print("임시 데이터 삽입 시도 (롤백될 예정)")
                # 의도적으로 오류 발생
                raise ValueError("테스트 목적의 강제 오류")
        except ValueError as e:
            # __exit__에서 롤백 메시지가 출력될 것이므로 여기서는 간단히 처리
            print(f"예상된 오류 발생 확인: {e}")
        except sqlite3.Error as e:
            # 삽입 중 다른 DB 오류 발생 시
            print(f"데이터베이스 오류 발생: {e}")
        print("--- 오류 발생 테스트 종료 ---")
        sys.exit(0) # 테스트 후 종료

    elif args.input:
        # 입력 루프는 메인 블록에서 처리
        current_name = args.input
        while not add_name(db_manager, current_name):
            try:
                # 사용자에게 명확한 프롬프트 제공
                new_input = input(f"'{current_name}'은(는) 이미 존재합니다. 다른 이름을 입력하세요 (취소하려면 Enter): ")
                if not new_input: # Enter만 입력 시 루프 종료
                    print("이름 추가가 취소되었습니다.")
                    break
                current_name = new_input # 새 이름으로 업데이트
            except EOFError: # Ctrl+D 등으로 입력 종료 시
                print("\n입력이 중단되었습니다.")
                break
    elif args.update:
        # nargs=2로 변경되었으므로 'to' 키워드 처리 로직 불필요
        old_name, new_name = args.update
        update_name(db_manager, old_name, new_name)
    elif args.delete:
        delete_name(db_manager, args.delete)
    elif args.output:
        print_all_names(db_manager)

if __name__ == "__main__":
    main()
