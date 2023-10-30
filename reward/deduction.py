from reward.utils import is_terminal

def decduction_same_symbol(generate_tree,pg):
     symbol = generate_tree.app
     
     if(len(generate_tree.args)==0):
          return 0
     
     elif(is_terminal(pg,generate_tree.args[0].app) and is_terminal(pg,generate_tree.args[1].app)):
          if symbol == 'bvand' or 'xor'  or 'bvsub' or 'eq' or 'uneq' or 'bvor':
               if((generate_tree.args[0].app ==generate_tree.args[1].app)):
                    return -0.5
               elif (('const' in generate_tree.args[0].app) and 
                    ('const' in generate_tree.args[1].app)):
                    return -0.5
               else:
                    return 0 
          elif symbol == 'bvadd':
               return 0
     else:
          if(len(generate_tree.args)==1):
               reward = decduction_same_symbol(generate_tree.args[0],pg)
          else:
               assert len(generate_tree.args)==2
               reward_left = decduction_same_symbol(generate_tree.args[0],pg)
               reward_right = decduction_same_symbol(generate_tree.args[1],pg)
               reward = reward_left + reward_right
                    

          return reward
     
# def decduction_repeat_eq(generate_tree,pg):
#      symbol = generate_tree.app
#      # assert symbol == 'eq' or 'uneq'
#      left = []
#      right = []
#      if(len(generate_tree.args)==0):
#           return [],[]

#      elif(is_terminal(pg,generate_tree.args[0].app) and is_terminal(pg,generate_tree.args[1].app)):
#           return [generate_tree.args[0].app],[generate_tree.args[1].app]
#      elif(is_terminal(pg,generate_tree.args[0].app)):
#           right_1, right_2 = decduction_repeat_eq(generate_tree.args[1],pg)
#           right = right_1 + right_2
#           return [generate_tree.args[0].app],right
#      elif(is_terminal(pg,generate_tree.args[1].app)):
#           left_1,left_2 = decduction_repeat_eq(generate_tree.args[0],pg) 
#           left  = left_1 + left_2
#           return left, [generate_tree.args[1].app]
#      else:
#           assert len(generate_tree.args)==2
          
#           left_1,left_2 = decduction_repeat_eq(generate_tree.args[0],pg) 
#           left  = left_1 + left_2
#           right_1, right_2 = decduction_repeat_eq(generate_tree.args[1],pg)
#           right = right_1 + right_2

     
#           return left, right 
def get_all_var(generate_tree,pg):
     symbol = generate_tree.app
     # assert symbol == 'eq' or 'uneq'
     left = []
     right = []
     if(len(generate_tree.args)==0):
          return [],[]

     elif(is_terminal(pg,generate_tree.args[0].app) and is_terminal(pg,generate_tree.args[1].app)):
          return [generate_tree.args[0].app],[generate_tree.args[1].app]
     elif(is_terminal(pg,generate_tree.args[0].app)):
          right_1, right_2 = get_all_var(generate_tree.args[1],pg)
          right = right_1 + right_2
          return [generate_tree.args[0].app],right
     elif(is_terminal(pg,generate_tree.args[1].app)):
          left_1,left_2 = get_all_var(generate_tree.args[0],pg) 
          left  = left_1 + left_2
          return left, [generate_tree.args[1].app]
     else:
          assert len(generate_tree.args)==2
          
          left_1,left_2 = get_all_var(generate_tree.args[0],pg) 
          left  = left_1 + left_2
          right_1, right_2 = get_all_var(generate_tree.args[1],pg)
          right = right_1 + right_2

     
          return left, right 


def width_match(pg, generate_tree,dictionary):
     symbol = generate_tree.app
     width_left = 0
     width_right = 0
     is_mismatch_left = False
     is_mismatch_right = False
     if(is_terminal(pg,symbol) and ('const' not in symbol)):
          width = len(dictionary[symbol][0])
          return width , False
     if(len(generate_tree.args) == 2):
          width_left, is_mismatch_left = width_match( pg, generate_tree.args[0],dictionary)
          width_right, is_mismatch_right = width_match( pg, generate_tree.args[1],dictionary)
     
     if(is_mismatch_left == True or is_mismatch_right == True):
          return 0, True
     else:
          if((width_left != width_right) and (width_left!=0) and (width_right!=0)):
               return 0, True
          else:
               if(symbol =='eq' or symbol =='uneq'):
                    return 1, False
               else:
                    # assert (( (width_left!=0) and (width_right!=0)))
                    width = width_left if width_left!=0 else width_right
                    return width, False
     

def deduction(generate_tree,pg,dictionary):
     # left,right = decduction_repeat_eq(generate_tree,pg)
     # set_left = set(left)
     # set_right = set(right)
     # common_elements = set_left & set_right
     # num_common_elements = len(common_elements)
     # rewards_eq = num_common_elements*-1
     rewards = decduction_same_symbol(generate_tree,pg)
     # rewards = rewards_eq + rewards_same
     width,is_mismatch = width_match(pg, generate_tree,dictionary)
     reward_width = -1 if(is_mismatch ==True) else 0
     
     return rewards ,reward_width