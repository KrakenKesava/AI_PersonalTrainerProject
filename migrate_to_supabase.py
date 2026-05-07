import os
import json
import glob
from dotenv import load_dotenv
from supabase import create_client, Client

def migrate_sessions():
    load_dotenv()
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    supabase: Client = create_client(url, key)
    
    sessions_dir = os.path.join(os.path.dirname(__file__), "sessions")
    json_files = glob.glob(os.path.join(sessions_dir, "*.json"))
    
    print(f"Found {len(json_files)} session files to migrate.\n")
    
    success_count = 0
    
    for filepath in json_files:
        filename = os.path.basename(filepath)
        print(f"Migrating {filename}...")
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                                 
            session_data = {
                "exercise": data.get("exercise", "unknown"),
                "session_date": data.get("date", "1970-01-01 00:00:00"),
                "total_reps": data.get("total_reps", len(data.get("reps", [])))
            }
            
            session_response = supabase.table("workout_sessions").insert(session_data).execute()
            
            if not session_response.data:
                print(f"  [!] Failed to insert session for {filename}")
                continue
                
            session_id = session_response.data[0]['id']
            print(f"  [+] Created session {session_id}")
            
                                                 
            reps_to_insert = []
            for rep in data.get("reps", []):
                reps_to_insert.append({
                    "session_id": session_id,
                    "rep_num": rep.get("rep_num"),
                    "rep_timestamp": rep.get("timestamp"),
                    "rom": rep.get("rom"),
                    "tempo": rep.get("tempo"),
                    "success": rep.get("success", False),
                    "feedback": rep.get("feedback", [])
                })
                
            if reps_to_insert:
                reps_response = supabase.table("workout_reps").insert(reps_to_insert).execute()
                print(f"  [+] Migrated {len(reps_response.data)} reps")
            
            success_count += 1
            print(f"  [v] Done with {filename}\n")
            
        except Exception as e:
            print(f"  [X] Error migrating {filename}: {e}\n")

    print(f"Migration completed. {success_count}/{len(json_files)} files migrated successfully.")

if __name__ == "__main__":
    migrate_sessions()
