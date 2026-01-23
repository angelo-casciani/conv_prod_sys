import pandas as pd
import re

def process_event_log(input_file, output_file):
    """
    Processa il log degli eventi aggiungendo trace_id e gestendo i part_id duplicati.
    
    Args:
        input_file (str): Path del file CSV di input
        output_file (str): Path del file CSV di output
    """
    
    # Leggi il CSV
    df = pd.read_csv(input_file)
    
    # Ordina per tempo per garantire l'ordine cronologico
    df = df.sort_values('time').reset_index(drop=True)
    
    # Estrai il numero dal part_id (es: 'p1' -> 1)
    df['part_num'] = df['part_id'].str.extract(r'p(\d+)').astype(int)
    
    # Traccia i part_id che sono già entrati nel processo
    entered_parts = set()
    max_part_num = 0
    
    # Mappa per tenere traccia delle rinominazioni: original_part_id -> current_part_id
    part_id_mapping = {}
    
    print("Processando le righe...")
    
    for idx, row in df.iterrows():
        original_part_id = row['part_id']
        current_part_num = row['part_num']
        station = row['station_id']
        activity = row['activity']
        
        # Applica la mappatura se esiste
        if original_part_id in part_id_mapping:
            current_part_id = part_id_mapping[original_part_id]
        else:
            current_part_id = original_part_id
        
        # Se siamo in corner2 con attività RETURN (primo evento del part_id in corner2)
        if station == 'corner2' and activity == 'RETURN':
            # Se questo part_id è già entrato nel processo, assegna un nuovo numero
            if current_part_num in entered_parts:
                max_part_num += 1
                new_part_id = f'p{max_part_num}'
                
                # Aggiorna la mappatura per questo part_id
                part_id_mapping[original_part_id] = new_part_id
                current_part_id = new_part_id
                
                print(f"Riga {idx}: {original_part_id} già presente, rinominato in {new_part_id}")
            else:
                # Primo ingresso di questo part_id
                entered_parts.add(current_part_num)
                max_part_num = max(max_part_num, current_part_num)
        
        # Aggiorna il part_id nella riga corrente
        df.iloc[idx, df.columns.get_loc('part_id')] = current_part_id
        # df.iloc[idx,df.columns.get_loc('activity')] = station.strip() + "_" + activity.strip()
    
    # Aggiorna la colonna part_id (è già stata modificata nel loop)
    # Ricalcola part_num dopo le modifiche
    df['part_num'] = df['part_id'].str.extract(r'p(\d+)').astype(int)
    
    df['trace_id'] = df['part_num'].astype(str) + '-' + df['part_id']
    
    df['concept:name'] = df['station_id']
    
    df['lifecycle:transition'] = 'complete'
    
    df['org:resource'] = df['station_id'].astype(str) + '_' + df['activity'].astype(str)

    df['lifecycle'] = df['org:resource']

    # Riordina le colonne: trace_id, poi le altre
    columns_order = ['trace_id'] + [col for col in df.columns if col not in ['trace_id', 'part_num']]
    df = df[columns_order]
    
    # # Rimuovi la colonna ausiliaria part_num
    # df = df.drop('part_num', axis=1)
    
    # Salva il risultato (rimuovendo activity e part_id)
    df_to_save = df.drop(['activity', 'part_id'], axis=1)
    df_to_save.to_csv(output_file, index=False)
    
    print(f"\nFile processato salvato in: {output_file}")
    print(f"Numero totale di righe: {len(df)}")
    print(f"Trace IDs unici: {sorted(df['trace_id'].unique())}")
    print(f"Mappature applicate: {len([k for k, v in part_id_mapping.items() if k != v])}")
    
    return df

def analyze_part_id_transitions(df):
    """
    Analizza le transizioni dei part_id per verificare la correttezza.
    """
    print("\n=== ANALISI TRANSIZIONI PART_ID ===")
    
    # Raggruppa eventi consecutivi per lo stesso part_id originale
    transitions = []
    current_group = []
    
    for idx, row in df.iterrows():
        if not current_group or current_group[-1]['part_id'] == row['part_id']:
            current_group.append({
                'idx': idx,
                'time': row['time'],
                'station_id': row['station_id'],
                'part_id': row['part_id'],
                'activity': row['activity']
            })
        else:
            if current_group:
                transitions.append(current_group)
            current_group = [{
                'idx': idx,
                'time': row['time'],
                'station_id': row['station_id'],
                'part_id': row['part_id'],
                'activity': row['activity']
            }]
    
    if current_group:
        transitions.append(current_group)
    
    # Mostra le transizioni
    for i, group in enumerate(transitions[:10]):  # Mostra solo le prime 10
        part_id = group[0]['part_id']
        start_station = group[0]['station_id']
        end_station = group[-1]['station_id']
        num_events = len(group)
        
        print(f"Gruppo {i+1}: {part_id} - {num_events} eventi ({start_station} → {end_station})")
        
        # Mostra dettagli se inizia con corner2 RETURN
        if group[0]['station_id'] == 'corner2' and group[0]['activity'] == 'RETURN':
            print(f"  → Nuovo ingresso in corner2")



def analyze_traces(df):
    """
    Analizza le tracce per verificare la correttezza del processamento.
    """
    print("\n=== ANALISI DELLE TRACCE ===")
    
    # Raggruppa per trace_id
    for trace_id in sorted(df['trace_id'].unique()):
        trace_data = df[df['trace_id'] == trace_id].sort_values('time')
        part_ids = trace_data['part_id'].unique()
        
        print(f"\nTrace {trace_id}:")
        print(f"  Part IDs: {list(part_ids)}")
        print(f"  Numero eventi: {len(trace_data)}")
        print(f"  Stazioni attraversate: {list(trace_data['station_id'].unique())}")
        
        # Verifica ingressi in corner2 con RETURN
        corner2_returns = trace_data[
            (trace_data['station_id'] == 'corner2') & 
            (trace_data['activity'] == 'RETURN')
        ]
        print(f"  Ingressi in corner2 (RETURN): {len(corner2_returns)}")

# Esempio di utilizzo
if __name__ == "__main__":
    input_file = "event_log_250905_123005.csv"
    output_file = "event_log_processed_1.csv"
    
    # Processa il file
    processed_df = process_event_log(input_file, output_file)
    
    # Analizza i risultati
    analyze_traces(processed_df)
    analyze_part_id_transitions(processed_df)
    
    # Mostra le prime righe del risultato
    print("\n=== PRIME RIGHE DEL FILE PROCESSATO ===")
    print(processed_df.head(10))