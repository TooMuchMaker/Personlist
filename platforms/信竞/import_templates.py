import re
import json
import os
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'knowledge.json'
CODEFORCES_DIR = BASE_DIR.parent / 'codeforces-go-1.2.0' / 'codeforces-go-1.2.0' / 'copypasta'
API_BASE = 'http://127.0.0.1:5003/api'

CATEGORY_MAPPING = {
    'graph.go': {'category_id': 5, 'name': '图论'},
    'graph_tree.go': {'category_id': 5, 'subcategory_id': 6, 'name': '图论-树上问题'},
    'math.go': {'category_id': 3, 'subcategory_id': 1, 'name': '数学-数论'},
    'math_fft.go': {'category_id': 3, 'subcategory_id': 3, 'name': '数学-FFT/NTT'},
    'math_ntt.go': {'category_id': 3, 'subcategory_id': 3, 'name': '数学-FFT/NTT'},
    'math_matrix.go': {'category_id': 3, 'subcategory_id': 4, 'name': '数学-线性代数'},
    'math_continued_fraction.go': {'category_id': 3, 'subcategory_id': 7, 'name': '数学-其他'},
    'math_fwt.go': {'category_id': 3, 'subcategory_id': 3, 'name': '数学-FFT/NTT'},
    'math_numerical_analysis.go': {'category_id': 3, 'subcategory_id': 7, 'name': '数学-其他'},
    'dp.go': {'category_id': 4, 'name': '动态规划'},
    'strings.go': {'category_id': 2, 'name': '字符串'},
    'trie.go': {'category_id': 2, 'subcategory_id': 4, 'name': '字符串-字典树'},
    'trie01.go': {'category_id': 2, 'subcategory_id': 4, 'name': '字符串-字典树'},
    'search.go': {'category_id': 6, 'name': '搜索'},
    'geometry.go': {'category_id': 3, 'subcategory_id': 5, 'name': '数学-计算几何'},
    'games.go': {'category_id': 3, 'subcategory_id': 6, 'name': '数学-博弈论'},
    'sort.go': {'category_id': 7, 'subcategory_id': 3, 'name': '其他算法-分治'},
    'bits.go': {'category_id': 7, 'subcategory_id': 4, 'name': '其他算法-位运算'},
    'rand.go': {'category_id': 7, 'subcategory_id': 5, 'name': '其他算法-随机算法'},
    'misc.go': {'category_id': 7, 'subcategory_id': 6, 'name': '其他算法-杂项'},
    'big.go': {'category_id': 3, 'subcategory_id': 7, 'name': '数学-其他'},
    'union_find.go': {'category_id': 1, 'subcategory_id': 3, 'name': '数据结构-并查集'},
    'fenwick_tree.go': {'category_id': 1, 'subcategory_id': 4, 'name': '数据结构-树状数组'},
    'segment_tree.go': {'category_id': 1, 'subcategory_id': 5, 'name': '数据结构-线段树'},
    'heap.go': {'category_id': 1, 'subcategory_id': 2, 'name': '数据结构-堆/优先队列'},
    'deque.go': {'category_id': 1, 'subcategory_id': 1, 'name': '数据结构-栈与队列'},
    'monotone_queue.go': {'category_id': 1, 'subcategory_id': 1, 'name': '数据结构-栈与队列'},
    'monotone_stack.go': {'category_id': 1, 'subcategory_id': 1, 'name': '数据结构-栈与队列'},
    'sparse_table.go': {'category_id': 1, 'subcategory_id': 7, 'name': '数据结构-其他'},
    'sqrt_decomposition.go': {'category_id': 1, 'subcategory_id': 7, 'name': '数据结构-其他'},
    'mo.go': {'category_id': 1, 'subcategory_id': 7, 'name': '数据结构-其他'},
    'bst.go': {'category_id': 1, 'subcategory_id': 6, 'name': '数据结构-平衡树'},
    'treap.go': {'category_id': 1, 'subcategory_id': 6, 'name': '数据结构-平衡树'},
    'splay.go': {'category_id': 1, 'subcategory_id': 6, 'name': '数据结构-平衡树'},
    'red_black_tree.go': {'category_id': 1, 'subcategory_id': 6, 'name': '数据结构-平衡树'},
    'scapegoat_tree.go': {'category_id': 1, 'subcategory_id': 6, 'name': '数据结构-平衡树'},
    'leftist_tree.go': {'category_id': 1, 'subcategory_id': 2, 'name': '数据结构-堆/优先队列'},
    'cartesian_tree.go': {'category_id': 1, 'subcategory_id': 6, 'name': '数据结构-平衡树'},
    'kd_tree.go': {'category_id': 1, 'subcategory_id': 7, 'name': '数据结构-其他'},
    'link_cut_tree.go': {'category_id': 1, 'subcategory_id': 6, 'name': '数据结构-平衡树'},
    'odt.go': {'category_id': 1, 'subcategory_id': 7, 'name': '数据结构-其他'},
    'odt_bst.go': {'category_id': 1, 'subcategory_id': 7, 'name': '数据结构-其他'},
    'pq_tree.go': {'category_id': 1, 'subcategory_id': 7, 'name': '数据结构-其他'},
    'common.go': {'category_id': 7, 'subcategory_id': 6, 'name': '其他算法-杂项'},
    'io.go': {'category_id': 7, 'subcategory_id': 6, 'name': '其他算法-杂项'},
}

SUBCATEGORY_KEYWORDS = {
    5: {
        1: ['最短路', 'dijkstra', 'spfa', 'floyd', 'bellman', 'shortest', 'bfs0', '01bfs'],
        2: ['最小生成树', 'mst', 'kruskal', 'prim', '生成树'],
        3: ['网络流', 'dinic', 'isap', 'hlpp', 'flow', 'maxflow', 'mincut', '费用流', 'mcmf'],
        4: ['强连通', 'scc', 'tarjan', 'kosaraju', '缩点', '2sat', '双连通', '割点', '桥', '边双', '点双'],
        5: ['二分图', 'matching', 'hungarian', 'hopcroft', 'km', '匹配', 'bipartite', '匈牙利'],
        6: ['lca', '树链剖分', '重链剖分', '树上', '树直径', '树重心', '树hash', 'euler', '欧拉', '树dp'],
        7: ['拓扑', 'topo', '欧拉回路', '欧拉路径', 'euler']
    },
    4: {
        1: ['背包', 'knapsack', 'pack', '01背包', '完全背包', '多重背包', '分组背包'],
        2: ['lis', 'lcs', '最长', '线性dp', 'edit', '编辑距离'],
        3: ['区间dp', '区间', 'matrixchain', '石子合并'],
        4: ['状压', 'state', 'bitmask', 'maskdp'],
        5: ['数位dp', '数位', 'digitdp'],
        6: ['树形dp', 'treedp', '树dp'],
        7: ['优化', 'convex', '斜率', '四边形', 'wqs', '分治dp', '数据结构优化']
    },
    2: {
        1: ['hash', '哈希', '字符串哈希', 'rolling'],
        2: ['kmp', 'border', 'next', 'fail'],
        3: ['后缀数组', 'sa', 'suffix', '后缀自动机', 'sam', '后缀树'],
        4: ['trie', '字典树'],
        5: ['ac自动机', 'acam', 'ahocorasick'],
        6: ['manacher', 'zfunc', 'z-function', '回文', 'palindrome', '最小表示法']
    },
    3: {
        1: ['gcd', 'lcm', '质数', 'prime', '素数', '筛', 'sieve', '欧拉函数', 'euler', 'phi', '因数', 'divisor', '约数', '分解', 'factor'],
        2: ['组合', 'combin', 'c(n', 'cnk', '排列', 'permut', 'stirling', '卡特兰', 'catalan', '容斥', 'inclusion'],
        3: ['fft', 'ntt', 'fwt', '卷积', 'convol', '多项式', 'polynomial'],
        4: ['矩阵', 'matrix', '高斯', 'gauss', '行列式', 'determinant', '线性基', 'linearbasis'],
        5: ['几何', 'geometry', '凸包', 'convex', '线段交', '点线', '圆'],
        6: ['博弈', 'game', 'nim', 'sg', 'sprague', 'grundy'],
        7: ['分数', 'fraction', '连分数', '数值']
    },
    1: {
        1: ['栈', 'stack', '队列', 'queue', '单调栈', '单调队列', 'monotone'],
        2: ['堆', 'heap', '优先队列', 'priority', '左偏树', 'leftist'],
        3: ['并查集', 'unionfind', 'dsu'],
        4: ['树状数组', 'fenwick', 'bit', 'binaryindexed'],
        5: ['线段树', 'segmenttree', 'segment', 'lazy', '懒标记'],
        6: ['平衡树', 'treap', 'splay', '红黑树', 'avl', '替罪羊', 'scapegoat', 'bst'],
        7: ['分块', 'sqrt', '莫队', 'odt', 'sparse', 'st表', 'kd树']
    },
    6: {
        1: ['dfs', 'bfs', '搜索', 'search', 'flood'],
        2: ['剪枝', 'prune', 'branch'],
        3: ['迭代加深', 'iterative', 'ida'],
        4: ['启发式', 'heuristic', 'astar', 'a*', 'ida*'],
        5: ['双向', 'bidirectional', 'meet']
    }
}

def extract_functions(content):
    functions = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        func_match = re.match(r'^func\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(', line)
        if func_match:
            func_name = func_match.group(1)
            
            comment_lines = []
            j = i - 1
            while j >= 0 and (lines[j].strip().startswith('//') or lines[j].strip() == ''):
                if lines[j].strip().startswith('//'):
                    comment_lines.insert(0, lines[j].strip()[2:].strip())
                j -= 1
            
            brace_count = 0
            func_code_lines = []
            started = False
            
            for k in range(i, len(lines)):
                code_line = lines[k]
                func_code_lines.append(code_line)
                
                for ch in code_line:
                    if ch == '{':
                        brace_count += 1
                        started = True
                    elif ch == '}':
                        brace_count -= 1
                
                if started and brace_count == 0:
                    break
            
            func_code = '\n'.join(func_code_lines)
            
            if not func_name.startswith('_') and len(func_code) > 50:
                functions.append({
                    'name': func_name,
                    'description': '\n'.join(comment_lines) if comment_lines else '',
                    'code': func_code
                })
            
            i += len(func_code_lines)
        else:
            i += 1
    
    return functions

def extract_type_structs(content):
    structs = []
    
    type_pattern = r'type\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:struct|interface)'
    
    for match in re.finditer(type_pattern, content):
        type_name = match.group(1)
        
        start = match.start()
        brace_count = 0
        end = start
        found_brace = False
        
        for i in range(start, len(content)):
            if content[i] == '{':
                brace_count += 1
                found_brace = True
            elif content[i] == '}':
                brace_count -= 1
            
            if found_brace and brace_count == 0:
                end = i + 1
                break
        
        struct_code = content[start:end]
        
        comment_lines = []
        lines_before = content[:start].split('\n')
        for line in reversed(lines_before):
            if line.strip().startswith('//'):
                comment_lines.insert(0, line.strip()[2:].strip())
            elif line.strip() == '':
                continue
            else:
                break
        
        if len(struct_code) > 30:
            structs.append({
                'name': type_name,
                'description': '\n'.join(comment_lines) if comment_lines else '',
                'code': struct_code
            })
    
    return structs

def determine_subcategory(category_id, name, code, description):
    code_lower = code.lower()
    name_lower = name.lower()
    desc_lower = description.lower()
    combined = name_lower + ' ' + code_lower + ' ' + desc_lower
    
    if category_id in SUBCATEGORY_KEYWORDS:
        for sub_id, keywords in SUBCATEGORY_KEYWORDS[category_id].items():
            for kw in keywords:
                if kw.lower() in combined:
                    return sub_id
    
    return None

def extract_file_comment(content):
    lines = content.split('\n')
    comment_lines = []
    
    in_block_comment = False
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('/*'):
            in_block_comment = True
            comment_lines.append(stripped[2:].strip())
            continue
        
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
                idx = stripped.find('*/')
                comment_lines.append(stripped[:idx].strip())
                break
            else:
                comment_lines.append(stripped)
        elif stripped.startswith('//'):
            comment_lines.append(stripped[2:].strip())
        elif stripped.startswith('package'):
            break
        elif stripped == '':
            continue
        else:
            break
    
    return '\n'.join(comment_lines)

def parse_go_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(filepath)
    
    if filename not in CATEGORY_MAPPING:
        return None
    
    mapping = CATEGORY_MAPPING[filename]
    category_id = mapping['category_id']
    default_subcategory = mapping.get('subcategory_id')
    
    file_comment = extract_file_comment(content)
    
    functions = extract_functions(content)
    structs = extract_type_structs(content)
    
    templates = []
    
    for func in functions:
        subcategory_id = default_subcategory
        if not subcategory_id:
            subcategory_id = determine_subcategory(category_id, func['name'], func['code'], func['description'])
        
        templates.append({
            'name': func['name'],
            'category_id': category_id,
            'subcategory_id': subcategory_id,
            'description': func['description'] or f"来自 {filename}",
            'code': func['code'],
            'language': 'go',
            'source_file': filename
        })
    
    for struct in structs:
        subcategory_id = default_subcategory
        if not subcategory_id:
            subcategory_id = determine_subcategory(category_id, struct['name'], struct['code'], struct['description'])
        
        templates.append({
            'name': struct['name'],
            'category_id': category_id,
            'subcategory_id': subcategory_id,
            'description': struct['description'] or f"来自 {filename}",
            'code': struct['code'],
            'language': 'go',
            'source_file': filename
        })
    
    return templates

def import_templates():
    all_templates = []
    
    for filename in CATEGORY_MAPPING.keys():
        filepath = CODEFORCES_DIR / filename
        if filepath.exists():
            print(f"解析文件: {filename}")
            templates = parse_go_file(filepath)
            if templates:
                all_templates.extend(templates)
                print(f"  提取了 {len(templates)} 个模板")
        else:
            print(f"文件不存在: {filepath}")
    
    print(f"\n总共提取了 {len(all_templates)} 个模板")
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    existing_names = {t['name'] for t in data.get('templates', [])}
    
    max_id = max([t['id'] for t in data.get('templates', [])], default=0)
    
    added_count = 0
    for template in all_templates:
        if template['name'] not in existing_names:
            max_id += 1
            template['id'] = max_id
            template['created_at'] = '2024-01-01 00:00:00'
            template['updated_at'] = '2024-01-01 00:00:00'
            template['complexity'] = ''
            template['references'] = []
            template['problems'] = []
            
            data['templates'].append(template)
            existing_names.add(template['name'])
            added_count += 1
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"成功导入 {added_count} 个新模板")
    
    return added_count

if __name__ == '__main__':
    import_templates()
