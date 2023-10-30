def is_terminal(pg,symbol):
     if 'const' in symbol:
          symbol = 'const' 
     for i in range(len(pg.t_nodes)):
          if(symbol == pg.t_nodes[i].name and 
               pg.t_nodes[i].node_type == "Terminal"):
               return True
     
     return False