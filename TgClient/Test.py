#    Copyright (C) 2017 Christian Stemmle
#
#    This file is part of Mercury.
#
#    Mercury is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Mercury is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Mercury. If not, see <http://www.gnu.org/licenses/>.

import pyotherside

connect_state = 'wait'
connect_state = 'enter_number'
#connect_state = True

class TestClient():
    
    # login code
    def request_code(self, phonenumber=None):
        pass

    def send_code(self, code):
        #return 'pass_required'
        return True

    # Two-step verification
    def send_pass(self, password):
        return True

    def log_out(self):
        pass

    # request data
    def request_dialogs(self):
        dialogs_model = [ 
            {'name':'Chat1', 'entity_id':'chat_1'},
            {'name':'Chat2', 'entity_id':'chat_2'},
        ]    
        pyotherside.send('update_dialogs', dialogs_model)
        
    def request_messages(self, ID):        
        messages_model = [
            {'name':'User', 'message':'Hello, World!', 'time':'00:42'},
            {'name':'World', 'message':'Hey, how are you?', 'time':'00:43'},
        ]
        pyotherside.send('update_messages', messages_model)
