from reward.utils import is_terminal

def decduction_same_symbol(generate_tree,pg):
     symbol = generate_tree.app
     
     if(len(generate_tree.args)==0):
          return 0
     
     elif(is_terminal(pg,generate_tree.args[0].app) and is_terminal(pg,generate_tree.args[1].app)):
          if symbol == 'bvand' or 'xor'  or 'bvsub' or 'eq' or 'uneq' or 'bvor' or 'bvule' or 'bvuge':
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
def is_same_node(left,right,pg):
     if(is_terminal(pg,left.app) and (not is_terminal(pg,right.app))):
          return False
     elif(is_terminal(pg,right.app) and (not is_terminal(pg,left.app))):
          return False
     elif(is_terminal(pg,left.app) and is_terminal(pg,right.app)):
          if(left.app == right.app):
               return True
          elif(("const" in left.app) and ("const" in right.app)):
               return True
          else:
               return False     
     else:
          left_left = left.args[0]
          left_right =  left.args[1]
          right_left = right.args[0]
          right_right =  right.args[1]
          if(left.app == right.app):
               if((left_left.app == right_left.app) and (left_right.app == right_right.app)):
                    return True
               elif((left_right.app == right_left.app) and (left_left.app == right_right.app)):
                    return True
               elif ((("const" in left_left.app) and ("const" in right_left.app)) and (("const" in left_right.app) and ("const" in right_right.app))):
                    return True
               elif ((("const" in left_right.app) and ("const" in right_left.app)) and (("const" in left_left.app) and ("const" in right_right.app))):
                    return True
               else:
                    return False
          else:
               return False

def deduction_symmetric(left, right, pg, count ):
     if(count==0):
          assert right == None
          count = count + 1
          is_stmmetric = deduction_symmetric(left.args[0], left.args[1], pg, count )
          return is_stmmetric
     
     if(is_same_node(left,right,pg)):
          if(is_terminal(pg,left.app)):
               assert is_terminal(pg,right.app)
               return True
          is_stmmetric_1 = deduction_symmetric(left.args[0], right.args[0], pg, count )    
          is_stmmetric_2 = deduction_symmetric(left.args[1], right.args[1], pg, count )
          is_stmmetric_3 = deduction_symmetric(left.args[1], right.args[0], pg, count )
          is_stmmetric_4 = deduction_symmetric(left.args[0], right.args[1], pg, count )
          is_stmmetric = (is_stmmetric_1 and is_stmmetric_2 ) or (is_stmmetric_3 and is_stmmetric_4)   
          return is_stmmetric
     else:
          return False

def deduction_const_connection(generate_tree,pg,dictionary,const_masking):
     symbol = generate_tree.app
     
     if(len(generate_tree.args)==0):
          if(is_terminal(pg,symbol) and ('const' not in symbol)):
               width = len(dictionary[symbol][0])
               return 0 , width
          else:
               return 0,-1
     elif(is_terminal(pg,generate_tree.args[0].app) and 'const' in generate_tree.args[0].app):
          if 'const' in generate_tree.args[1].app:
               return -1,0
          elif symbol == 'bvand' or symbol == 'bvxor' or symbol == 'bvor':
               reward_right, width_right = deduction_const_connection(generate_tree.args[1],pg,dictionary,const_masking)
               if(((width_right not in const_masking) and width_right!=-1) or (reward_right==-1) or (len(const_masking)==0)):
                    return -1,0
               else:
                    return 0,width_right
          else:
               reward,width_right = deduction_const_connection(generate_tree.args[1],pg,dictionary,const_masking)
               if(symbol =='eq' or symbol =='bvule' or symbol =='bvuge'):
                    return reward,1
               else:
                    return reward,width_right
     
     elif(is_terminal(pg,generate_tree.args[1].app) and 'const' in generate_tree.args[1].app):
          if 'const' in generate_tree.args[0].app:
               return -1,0
          elif symbol == 'bvand' or symbol == 'bvxor' or symbol == 'bvor':
               reward_left, width_left = deduction_const_connection(generate_tree.args[1],pg,dictionary,const_masking)
               if(((width_left not in const_masking) and width_left!=-1) or (reward_left==-1)or (len(const_masking)==0)):
                    return -1,0
               else:
                    return 0,width_left
          else:
               reward,width_left = deduction_const_connection(generate_tree.args[0],pg,dictionary,const_masking)
               if(symbol =='eq' or symbol =='bvule' or symbol =='bvuge'):
                    return reward,1
               else:
                    return reward,width_left    
     else:
          # if(len(generate_tree.args)==1):
          #      reward = deduction_const_connection(generate_tree.args[0],pg)
          # else:
               assert len(generate_tree.args)==2
               reward_left,width_left = deduction_const_connection(generate_tree.args[0],pg,dictionary,const_masking)
               reward_right,width_right = deduction_const_connection(generate_tree.args[1],pg,dictionary,const_masking)
               reward = reward_left + reward_right               
               if(reward!=0):
                    assert width_left==0 or width_right==0
                    return reward,0
               else:
                    # assert width_left == width_right
                    if(symbol =='eq' or symbol =='bvule' or symbol =='bvuge'):
                         return reward,1
                    else:
                         return reward,width_left                            

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
               if(symbol =='eq' or symbol =='bvule' or symbol =='bvuge'):
                    return 1, False
               else:
                    # assert (( (width_left!=0) and (width_right!=0)))
                    width = width_left if width_left!=0 else width_right
                    return width, False
     

def deduction(generate_tree,pg,dictionary,const_masking):
     # left,right = decduction_repeat_eq(generate_tree,pg)
     # set_left = set(left)
     # set_right = set(right)
     # common_elements = set_left & set_right
     # num_common_elements = len(common_elements)
     # rewards_eq = num_common_elements*-1
     rewards = decduction_same_symbol(generate_tree,pg)
     # rewards = rewards_eq + rewards_same
     width,is_mismatch = width_match(pg, generate_tree,dictionary)
     if(is_mismatch ==True):
          return rewards, -1
     else:
          reward_const,width = deduction_const_connection(generate_tree,pg,dictionary,const_masking)
          return rewards , reward_const
