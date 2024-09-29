module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] y,
    output reg [10:0] x,
    output reg [10:0] i,
    output reg [10:0] n  

);


    
    always @(posedge clk) begin
        if(rst)begin
            x <= 0;
            y <= 0;
            i <= 0;
            n <= 40;
        end
        else begin
            if(selector&&( i< n))begin
                    i<= i + 1;
                    x<= x + 1;
                    y<= y + 2;
                    n<=n;
                
            end
            else if(~selector&&( i< n)) begin
                    i<= i + 1;
                    x<= x + 2;
                    y<= y + 1;
                    n<=n;
            
            end
            else begin
                y <= y;
                x<=x;
                n<=n;
                i<=i;
            end
        end

    end
    assert property (!((i>=n)&&(n*3!=x+y)));
endmodule