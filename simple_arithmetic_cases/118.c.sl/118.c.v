module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [7:0] x,
    output reg [7:0] y
);
    
    always @(posedge clk) begin
        if(rst)begin 
            x <= 5;
            y <= 0;
        end else begin
            if((selector))begin
                x<= x + 10;
                y <= y + 10;
            end
            else begin
                x<=x;
                y<=y;
            end
        
        end
        
    end
    assert property (!((y==0)&&(x==20)));
endmodule